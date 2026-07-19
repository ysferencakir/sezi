package com.sezi.bridge

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.BasalBodyTemperatureRecord
import androidx.health.connect.client.records.BasalMetabolicRateRecord
import androidx.health.connect.client.records.BloodGlucoseRecord
import androidx.health.connect.client.records.BloodPressureRecord
import androidx.health.connect.client.records.BodyFatRecord
import androidx.health.connect.client.records.BodyTemperatureRecord
import androidx.health.connect.client.records.BodyWaterMassRecord
import androidx.health.connect.client.records.BoneMassRecord
import androidx.health.connect.client.records.CervicalMucusRecord
import androidx.health.connect.client.records.CyclingPedalingCadenceRecord
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.ElevationGainedRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.FloorsClimbedRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.HeartRateVariabilityRmssdRecord
import androidx.health.connect.client.records.HeightRecord
import androidx.health.connect.client.records.HydrationRecord
import androidx.health.connect.client.records.IntermenstrualBleedingRecord
import androidx.health.connect.client.records.LeanBodyMassRecord
import androidx.health.connect.client.records.MenstruationFlowRecord
import androidx.health.connect.client.records.MenstruationPeriodRecord
import androidx.health.connect.client.records.NutritionRecord
import androidx.health.connect.client.records.OvulationTestRecord
import androidx.health.connect.client.records.OxygenSaturationRecord
import androidx.health.connect.client.records.PowerRecord
import androidx.health.connect.client.records.Record
import androidx.health.connect.client.records.RespiratoryRateRecord
import androidx.health.connect.client.records.RestingHeartRateRecord
import androidx.health.connect.client.records.SexualActivityRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.SpeedRecord
import androidx.health.connect.client.records.StepsCadenceRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.TotalCaloriesBurnedRecord
import androidx.health.connect.client.records.Vo2MaxRecord
import androidx.health.connect.client.records.WeightRecord
import androidx.health.connect.client.records.WheelchairPushesRecord
import androidx.health.connect.client.request.AggregateGroupByPeriodRequest
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.time.LocalDate
import java.time.Period
import java.time.ZoneId
import java.time.temporal.TemporalAccessor
import kotlin.reflect.KClass

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
            HealthPermission.getReadPermission(WeightRecord::class),
            HealthPermission.getReadPermission(HeightRecord::class),
            HealthPermission.getReadPermission(BodyFatRecord::class),
            HealthPermission.getReadPermission(BloodGlucoseRecord::class),
            HealthPermission.getReadPermission(BloodPressureRecord::class),
            HealthPermission.getReadPermission(OxygenSaturationRecord::class),
            HealthPermission.getReadPermission(HydrationRecord::class),
            HealthPermission.getReadPermission(RestingHeartRateRecord::class),
            HealthPermission.getReadPermission(HeartRateVariabilityRmssdRecord::class),
            HealthPermission.getReadPermission(RespiratoryRateRecord::class),
            HealthPermission.getReadPermission(Vo2MaxRecord::class),
            HealthPermission.getReadPermission(FloorsClimbedRecord::class),
            HealthPermission.getReadPermission(BodyTemperatureRecord::class),
            HealthPermission.getReadPermission(ActiveCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(BasalBodyTemperatureRecord::class),
            HealthPermission.getReadPermission(BasalMetabolicRateRecord::class),
            HealthPermission.getReadPermission(BodyWaterMassRecord::class),
            HealthPermission.getReadPermission(BoneMassRecord::class),
            HealthPermission.getReadPermission(CervicalMucusRecord::class),
            HealthPermission.getReadPermission(CyclingPedalingCadenceRecord::class),
            HealthPermission.getReadPermission(ElevationGainedRecord::class),
            HealthPermission.getReadPermission(IntermenstrualBleedingRecord::class),
            HealthPermission.getReadPermission(LeanBodyMassRecord::class),
            HealthPermission.getReadPermission(MenstruationFlowRecord::class),
            HealthPermission.getReadPermission(MenstruationPeriodRecord::class),
            HealthPermission.getReadPermission(NutritionRecord::class),
            HealthPermission.getReadPermission(OvulationTestRecord::class),
            HealthPermission.getReadPermission(PowerRecord::class),
            HealthPermission.getReadPermission(SexualActivityRecord::class),
            HealthPermission.getReadPermission(SpeedRecord::class),
            HealthPermission.getReadPermission(StepsCadenceRecord::class),
            HealthPermission.getReadPermission(WheelchairPushesRecord::class),
            HealthPermission.PERMISSION_READ_HEALTH_DATA_IN_BACKGROUND,
        )

        /** Health Connect 1.1.0'ın kararlı sürümünde okunabilen tüm kayıt türleri. */
        private val RECORD_TYPES: List<KClass<out Record>> = listOf(
            ActiveCaloriesBurnedRecord::class,
            BasalBodyTemperatureRecord::class,
            BasalMetabolicRateRecord::class,
            BloodGlucoseRecord::class,
            BloodPressureRecord::class,
            BodyFatRecord::class,
            BodyTemperatureRecord::class,
            BodyWaterMassRecord::class,
            BoneMassRecord::class,
            CervicalMucusRecord::class,
            CyclingPedalingCadenceRecord::class,
            DistanceRecord::class,
            ElevationGainedRecord::class,
            ExerciseSessionRecord::class,
            FloorsClimbedRecord::class,
            HeartRateRecord::class,
            HeartRateVariabilityRmssdRecord::class,
            HeightRecord::class,
            HydrationRecord::class,
            IntermenstrualBleedingRecord::class,
            LeanBodyMassRecord::class,
            MenstruationFlowRecord::class,
            MenstruationPeriodRecord::class,
            NutritionRecord::class,
            OvulationTestRecord::class,
            OxygenSaturationRecord::class,
            PowerRecord::class,
            RespiratoryRateRecord::class,
            RestingHeartRateRecord::class,
            SexualActivityRecord::class,
            SleepSessionRecord::class,
            SpeedRecord::class,
            StepsCadenceRecord::class,
            StepsRecord::class,
            TotalCaloriesBurnedRecord::class,
            Vo2MaxRecord::class,
            WeightRecord::class,
            WheelchairPushesRecord::class,
        )

        fun sdkAvailable(context: Context): Boolean =
            HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE
    }

    suspend fun hasAllPermissions(): Boolean {
        // Arka plan okuma izni cihaza göre reddedilebilir; onu zorunlu sayma —
        // yoksa yalnızca arka plan senkronu etkilenir, ön plan "Şimdi Gönder" çalışır.
        val required = PERMISSIONS - HealthPermission.PERMISSION_READ_HEALTH_DATA_IN_BACKGROUND
        return client.permissionController.getGrantedPermissions().containsAll(required)
    }

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
        payload.put("raw_records", readAllRecords(start, end))
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

        enrichDailyRecords(arr, start, end, zone)
        return arr
    }

    private suspend fun enrichDailyRecords(arr: JSONArray, start: Instant, end: Instant, zone: ZoneId) {
        fun dayObject(dayKey: String): JSONObject {
            for (i in 0 until arr.length()) {
                val obj = arr.getJSONObject(i)
                if (obj.optString("day") == dayKey) return obj
            }
            val created = JSONObject().put("day", dayKey)
            arr.put(created)
            return created
        }

        fun attachValue(dayKey: String, key: String, value: Any?) {
            if (value == null) return
            dayObject(dayKey).put(key, value)
        }

        fun addValue(dayKey: String, key: String, value: Double?) {
            if (value == null) return
            val day = dayObject(dayKey)
            day.put(key, day.optDouble(key, 0.0) + value)
        }

        fun dayKeyFor(recordTime: Instant): String = recordTime.atZone(zone).toLocalDate().toString()

        client.readRecords(ReadRecordsRequest(WeightRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "weight_kg", it.weight.inKilograms) }
        client.readRecords(ReadRecordsRequest(HeightRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "height_cm", it.height.inMeters * 100) }
        client.readRecords(ReadRecordsRequest(BodyFatRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "body_fat_percent", it.percentage.value) }
        client.readRecords(ReadRecordsRequest(BloodGlucoseRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "blood_glucose_mmol", it.level.inMillimolesPerLiter) }
        client.readRecords(ReadRecordsRequest(BloodPressureRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach {
                attachValue(dayKeyFor(it.time), "blood_pressure_systolic", it.systolic.inMillimetersOfMercury)
                attachValue(dayKeyFor(it.time), "blood_pressure_diastolic", it.diastolic.inMillimetersOfMercury)
            }
        client.readRecords(ReadRecordsRequest(OxygenSaturationRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "oxygen_saturation_percent", it.percentage.value) }
        client.readRecords(ReadRecordsRequest(HydrationRecord::class, TimeRangeFilter.between(start, end)))
            .records.forEach { addValue(dayKeyFor(it.startTime), "hydration_liters", it.volume.inLiters) }
        client.readRecords(ReadRecordsRequest(RestingHeartRateRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "resting_heart_rate", it.beatsPerMinute) }
        client.readRecords(ReadRecordsRequest(HeartRateVariabilityRmssdRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "hrv_rmssd_ms", it.heartRateVariabilityMillis) }
        client.readRecords(ReadRecordsRequest(RespiratoryRateRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "respiratory_rate", it.rate) }
        client.readRecords(ReadRecordsRequest(Vo2MaxRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "vo2_max", it.vo2MillilitersPerMinuteKilogram) }
        client.readRecords(ReadRecordsRequest(FloorsClimbedRecord::class, TimeRangeFilter.between(start, end)))
            .records.forEach { addValue(dayKeyFor(it.startTime), "floors_climbed", it.floors) }
        client.readRecords(ReadRecordsRequest(BodyTemperatureRecord::class, TimeRangeFilter.between(start, end)))
            .records.sortedBy { it.time }
            .forEach { attachValue(dayKeyFor(it.time), "body_temperature_celsius", it.temperature.inCelsius) }
        client.readRecords(ReadRecordsRequest(NutritionRecord::class, TimeRangeFilter.between(start, end)))
            .records.forEach {
                val day = dayKeyFor(it.startTime)
                addValue(day, "nutrition_calories", it.energy?.inKilocalories)
                addValue(day, "nutrition_protein_g", it.protein?.inGrams)
                addValue(day, "nutrition_fat_g", it.totalFat?.inGrams)
                addValue(day, "nutrition_carbs_g", it.totalCarbohydrate?.inGrams)
            }
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

    /**
     * Her kayıt tipini ortak bir zarf içinde taşır. Alanlar yansıtma ile JSON'a
     * dönüştürüldüğü için SDK'ya yeni bir alan eklendiğinde köprü kodu değişmeden
     * sunucuya ulaşır.
     */
    @Suppress("UNCHECKED_CAST")
    private suspend fun readAllRecords(start: Instant, end: Instant): JSONArray {
        val arr = JSONArray()
        for (recordType in RECORD_TYPES) {
            try {
                val response = client.readRecords(
                    ReadRecordsRequest(
                        recordType = recordType as KClass<Record>,
                        timeRangeFilter = TimeRangeFilter.between(start, end),
                    )
                )
                for (record in response.records) {
                    arr.put(recordEnvelope(record))
                    if (arr.length() >= 2500) return arr
                }
            } catch (_: SecurityException) {
                // Kullanıcı belirli bir hassas veri grubuna izin vermediyse diğer
                // kayıt türlerini senkronlamaya devam et.
            } catch (_: UnsupportedOperationException) {
                // Eski Health Connect sağlayıcıları bazı kayıt türlerini desteklemeyebilir.
            }
        }
        return arr
    }

    private fun recordEnvelope(record: Record): JSONObject {
        val type = record.javaClass.simpleName.removeSuffix("Record")
        val startTime = getter(record, "time") ?: getter(record, "startTime")
        val endTime = getter(record, "endTime") ?: startTime
        val metadata = record.metadata
        val externalId = metadata.id.ifBlank {
            "${record.javaClass.simpleName}:${startTime ?: record.hashCode()}"
        }
        return JSONObject()
            .put("external_id", externalId)
            .put("record_type", record.javaClass.simpleName)
            .put("category", categoryFor(type))
            .put("title", type.replace(Regex("([a-z])([A-Z])"), "$1 $2"))
            .put("start_time", startTime?.toString())
            .put("end_time", endTime?.toString())
            .put("data", jsonObject(record, 0))
    }

    private fun categoryFor(type: String): String = when (type) {
        "Steps", "StepsCadence", "Distance", "ElevationGained", "FloorsClimbed",
        "ExerciseSession", "ActiveCaloriesBurned", "TotalCaloriesBurned",
        "CyclingPedalingCadence", "Power", "Speed", "Vo2Max", "WheelchairPushes" -> "activity"
        "Weight", "Height", "BodyFat", "BodyWaterMass", "BoneMass",
        "LeanBodyMass", "BasalMetabolicRate" -> "body"
        "Nutrition", "Hydration" -> "nutrition"
        "SleepSession" -> "sleep"
        "CervicalMucus", "IntermenstrualBleeding", "MenstruationFlow",
        "MenstruationPeriod", "OvulationTest", "SexualActivity",
        "BasalBodyTemperature" -> "cycle"
        else -> "vitals"
    }

    private fun getter(target: Any, property: String): Any? {
        val method = "get" + property.replaceFirstChar { it.uppercase() }
        return runCatching {
            target.javaClass.methods.firstOrNull { it.name == method && it.parameterCount == 0 }
                ?.invoke(target)
        }.getOrNull()
    }

    private fun jsonObject(target: Any, depth: Int): JSONObject {
        val obj = JSONObject()
        if (depth > 4) return obj.put("value", target.toString())
        target.javaClass.methods
            .asSequence()
            .filter {
                it.parameterCount == 0 &&
                    it.name != "getClass" &&
                    (it.name.startsWith("get") || it.name.startsWith("is"))
            }
            .sortedBy { it.name }
            .forEach { method ->
                val rawName = if (method.name.startsWith("get")) method.name.drop(3) else method.name.drop(2)
                val name = rawName.replaceFirstChar { it.lowercase() }
                runCatching { method.invoke(target) }.getOrNull()?.let {
                    obj.put(name, jsonValue(it, depth + 1))
                }
            }
        return obj
    }

    private fun jsonValue(value: Any?, depth: Int): Any = when (value) {
        null -> JSONObject.NULL
        is String, is Number, is Boolean -> value
        is Instant, is TemporalAccessor, is java.time.Duration, is java.time.ZoneOffset -> value.toString()
        is Enum<*> -> value.name
        is Map<*, *> -> JSONObject().also { obj ->
            value.entries.take(100).forEach { (key, item) ->
                obj.put(key.toString(), jsonValue(item, depth + 1))
            }
        }
        is Iterable<*> -> JSONArray().also { arr ->
            value.take(250).forEach { arr.put(jsonValue(it, depth + 1)) }
        }
        is Array<*> -> JSONArray().also { arr ->
            value.take(250).forEach { arr.put(jsonValue(it, depth + 1)) }
        }
        else -> {
            val packageName = value.javaClass.packageName
            if (depth <= 4 && packageName.startsWith("androidx.health.connect")) {
                jsonObject(value, depth)
            } else {
                value.toString()
            }
        }
    }
}
