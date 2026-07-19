package com.sezi.bridge

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.time.Instant
import java.util.concurrent.TimeUnit

/** 6 saatte bir Health Connect'ten okuyup Sezi'ye gönderir. */
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val prefs = applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val url = prefs.getString(KEY_URL, null) ?: return Result.failure()
        val token = prefs.getString(KEY_TOKEN, null) ?: return Result.failure()

        return try {
            val reader = HealthReader(applicationContext)
            if (!reader.hasAllPermissions()) return Result.failure()
            val payload = reader.buildPayload(days = 3)
            ApiClient.postIngest(url, token, payload)
            prefs.edit().putString(KEY_LAST_SYNC, Instant.now().toString()).apply()
            Result.success()
        } catch (e: Exception) {
            // Ağ/sunucu hatası — WorkManager backoff ile tekrar dener
            Result.retry()
        }
    }

    companion object {
        const val PREFS = "sezi_bridge"
        const val KEY_URL = "base_url"
        const val KEY_TOKEN = "ingest_token"
        const val KEY_LAST_SYNC = "last_sync"
        private const val WORK_NAME = "sezi_sync"

        fun schedule(context: Context) {
            val request = PeriodicWorkRequestBuilder<SyncWorker>(6, TimeUnit.HOURS)
                .setConstraints(
                    Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
                )
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME, ExistingPeriodicWorkPolicy.KEEP, request
            )
        }
    }
}
