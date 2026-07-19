package com.sezi.bridge

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Sezi backend'ine (POST /api/health/ingest) veri gönderir. */
object ApiClient {

    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .callTimeout(180, TimeUnit.SECONDS)
        .build()

    /** Başarıda sunucu yanıtını (özet JSON) döner, hatada exception fırlatır. */
    fun postIngest(baseUrl: String, token: String, payload: JSONObject): String {
        val url = baseUrl.trimEnd('/') + "/api/health/ingest"
        val request = Request.Builder()
            .url(url)
            .header("X-Ingest-Token", token)
            .post(payload.toString().toRequestBody("application/json".toMediaType()))
            .build()
        http.newCall(request).execute().use { response ->
            val body = response.body?.string() ?: ""
            if (!response.isSuccessful) {
                throw RuntimeException("HTTP ${response.code}: ${body.take(200)}")
            }
            return body
        }
    }
}
