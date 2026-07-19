package com.sezi.bridge

import android.content.Context
import android.os.Bundle
import android.text.InputType
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContract
import androidx.appcompat.app.AppCompatActivity
import androidx.health.connect.client.PermissionController
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var status: TextView
    private lateinit var urlInput: EditText
    private lateinit var tokenInput: EditText

    private val permissionLauncher = registerForActivityResult(
        PermissionController.createRequestPermissionResultContract() as ActivityResultContract<Set<String>, Set<String>>
    ) { granted ->
        setStatus(
            if (granted.containsAll(HealthReader.PERMISSIONS)) "İzinler tamam ✓"
            else "Eksik izin var — tekrar 'İzin İste'ye bas"
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getSharedPreferences(SyncWorker.PREFS, Context.MODE_PRIVATE)

        val pad = (16 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
        }

        root.addView(TextView(this).apply {
            text = "Sezi Bridge"
            textSize = 24f
        })
        root.addView(TextView(this).apply {
            text = "Samsung Health → Health Connect → Sezi · v${BuildConfig.VERSION_NAME}"
            textSize = 14f
        })

        urlInput = EditText(this).apply {
            hint = "Sunucu adresi (https://...)"
            setText(prefs.getString(SyncWorker.KEY_URL, "https://sezi.ysferencakir.info.tr"))
        }
        root.addView(urlInput)

        tokenInput = EditText(this).apply {
            hint = "Ingest token (HEALTH_INGEST_TOKEN)"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            setText(prefs.getString(SyncWorker.KEY_TOKEN, ""))
        }
        root.addView(tokenInput)

        root.addView(Button(this).apply {
            text = "Kaydet ve 6 saatlik senkronu kur"
            setOnClickListener { saveAndSchedule() }
        })
        root.addView(Button(this).apply {
            text = "Health Connect İzni İste"
            setOnClickListener { permissionLauncher.launch(HealthReader.PERMISSIONS) }
        })
        root.addView(Button(this).apply {
            text = "Şimdi Gönder (son 3 gün)"
            setOnClickListener { syncNow() }
        })

        status = TextView(this).apply {
            textSize = 14f
            setPadding(0, pad, 0, 0)
            text = "Son senkron: " + (prefs.getString(SyncWorker.KEY_LAST_SYNC, null) ?: "henüz yok")
        }
        root.addView(status)

        setContentView(ScrollView(this).apply { addView(root) })

        if (!HealthReader.sdkAvailable(this)) {
            setStatus("Health Connect bulunamadı — Play Store'dan kur veya sistem ayarlarından etkinleştir")
        }
    }

    private fun saveAndSchedule() {
        val url = urlInput.text.toString().trim()
        val token = tokenInput.text.toString().trim()
        if (url.isEmpty() || token.isEmpty()) {
            setStatus("URL ve token boş olamaz")
            return
        }
        getSharedPreferences(SyncWorker.PREFS, Context.MODE_PRIVATE).edit()
            .putString(SyncWorker.KEY_URL, url)
            .putString(SyncWorker.KEY_TOKEN, token)
            .apply()
        SyncWorker.schedule(this)
        setStatus("Kaydedildi — arka plan senkronu kuruldu (6 saatte bir)")
    }

    private fun syncNow() {
        val prefs = getSharedPreferences(SyncWorker.PREFS, Context.MODE_PRIVATE)
        val url = prefs.getString(SyncWorker.KEY_URL, null)
        val token = prefs.getString(SyncWorker.KEY_TOKEN, null)
        if (url == null || token == null) {
            setStatus("Önce kaydet")
            return
        }
        setStatus("Gönderiliyor…")
        lifecycleScope.launch {
            try {
                val reader = HealthReader(this@MainActivity)
                if (!reader.hasAllPermissions()) {
                    setStatus("İzinler eksik — önce 'Health Connect İzni İste'")
                    return@launch
                }
                val result = withContext(Dispatchers.IO) {
                    val payload = reader.buildPayload(days = 3)
                    ApiClient.postIngest(url, token, payload)
                }
                setStatus("Gönderildi ✓\n$result")
            } catch (e: Exception) {
                setStatus("HATA: ${e.message}")
            }
        }
    }

    private fun setStatus(text: String) {
        runOnUiThread { status.text = text }
    }
}
