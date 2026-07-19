package com.sezi.bridge

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.TotalCaloriesBurnedRecord
import androidx.health.connect.client.request.AggregateGroupByPeriodRequest
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.time.LocalDate
import java.time.Period
import java.time.ZoneId

/** Health Connect'ten okuyup /api/health/ingest payload'ı üretir. */
class HealthReader(context: Context) {

    private val client = HealthConnectClient.getOrCreate(context)

    companion object {
        val PERMISSIONS = setOf(
            HealthPermission.getReadPermission(StepsRecord::class),
            HealthPermission.getReadPermission(DistanceRecord::class),
            HealthPermission.getReadPermission(TotalCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(ExerciseSessionRecord::class),
            HealthPermission.getReadPermission(SleepSessionRecord::class),
            HealthPermission.getReadPermission(HeartRateRecord::class),
        )

        fun sdkAvailable(context: Context): Boolean =
            HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE
    }

    suspend fun hasAllPermissions(): Boolean =
        client.permissionController.getGrantedPermissions().containsAll(PERMISSIONS)

    /** Son [days] günün verisini ingest payload'ı (JSON) olarak toplar. */
    suspend fun buildPayload(days: Int): JSONObject {
        val zone = ZoneId.systemDefault()
        val today = LocalDate.now(zone)
        val start = today.minusDays(days.toLong() - 1).atStartOfDay(zone).toInstant()
        val end = Instant.now()

        val payload = JSONObject()
        payload.put("source", "health_connect")
        payload.put("days", readDailyAggregates(start, end, zone))
        payload.put("sleep_sessions", readSleep(start, end))
        payload.put("heart_rates", readHeartRates(start, end))
        return payload
    }

    private suspend fun readDailyAggregates(start: Instant, end: Instant, zone: ZoneId): JSONArray {
        val buckets = client.aggregateGroupByPeriod(
            AggregateGroupByPeriodRequest(
                metrics = setOf(
                    StepsRecord.COUNT_TOTAL,
                    DistanceRecord.DISTANCE_TOTAL,
                    TotalCaloriesBurnedRecord.ENERGY_TOTAL,
                    ExerciseSessionRecord.EXERCISE_DURATION_TOTAL,
                ),
                timeRangeFilter = TimeRangeFilter.between(
                    start.atZone(zone).toLocalDateTime(),
                    end.atZone(zone).toLocalDateTime(),
                ),
                timeRangeSlicer = Period.ofDays(1),
            )
        )
        val arr = JSONArray()
        for (bucket in buckets) {
            val day = JSONObject()
            day.put("day", bucket.startTime.toLocalDate().toString())
            bucket.result[StepsRecord.COUNT_TOTAL]?.let { day.put("steps", it) }
            bucket.result[DistanceRecord.DISTANCE_TOTAL]?.let { day.put("distance_meters", it.inMeters) }
            bucket.result[TotalCaloriesBurnedRecord.ENERGY_TOTAL]?.let { day.put("calories", it.inKilocalories) }
            bucket.result[ExerciseSessionRecord.EXERCISE_DURATION_TOTAL]?.let {
                day.put("active_minutes", it.toMinutes())
            }
            // Hiç metrik yoksa günü gönderme (boş gün, sunucudaki veriyi ezmesin)
            if (day.length() > 1) arr.put(day)
        }
        return arr
    }

    private suspend fun readSleep(start: Instant, end: Instant): JSONArray {
        val arr = JSONArray()
        val records = client.readRecords(
            ReadRecordsRequest(SleepSessionRecord::class, TimeRangeFilter.between(start, end))
        ).records
        for (session in records) {
            if (session.stages.isNotEmpty()) {
                for (stage in session.stages) {
                    arr.put(
                        JSONObject()
                            .put("start_time", stage.startTime.toString())
                            .put("end_time", stage.endTime.toString())
                            .put("stage", stageName(stage.stage))
                    )
                }
            } else {
                arr.put(
                    JSONObject()
                        .put("start_time", session.startTime.toString())
                        .put("end_time", session.endTime.toString())
                )
            }
        }
        return arr
    }

    private fun stageName(stage: Int): String? = when (stage) {
        SleepSessionRecord.STAGE_TYPE_AWAKE,
        SleepSessionRecord.STAGE_TYPE_AWAKE_IN_BED,
        SleepSessionRecord.STAGE_TYPE_OUT_OF_BED -> "awake"
        SleepSessionRecord.STAGE_TYPE_LIGHT -> "light"
        SleepSessionRecord.STAGE_TYPE_DEEP -> "deep"
        SleepSessionRecord.STAGE_TYPE_REM -> "rem"
        SleepSessionRecord.STAGE_TYPE_SLEEPING -> "light"
        else -> null
    }

    private suspend fun readHeartRates(start: Instant, end: Instant): JSONArray {
        val samples = mutableListOf<Pair<Instant, Long>>()
        val records = client.readRecords(
            ReadRecordsRequest(HeartRateRecord::class, TimeRangeFilter.between(start, end))
        ).records
        for (record in records) {
            for (sample in record.samples) {
                samples.add(sample.time to sample.beatsPerMinute)
            }
        }
        samples.sortBy { it.first }
        // Payload'ı makul tutmak için en fazla ~300 örnek gönder (eşit aralıklı seyreltme)
        val stride = maxOf(1, samples.size / 300)
        val arr = JSONArray()
        for (i in samples.indices step stride) {
            arr.put(
                JSONObject()
                    .put("measured_at", samples[i].first.toString())
                    .put("bpm", samples[i].second)
            )
        }
        return arr
    }
}
