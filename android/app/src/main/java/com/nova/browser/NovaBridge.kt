package com.nova.browser

import android.net.Uri
import android.util.Base64
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.activity.result.ActivityResultLauncher

class NovaBridge(
    private val activity: MainActivity,
    private val dataStore: DataStore,
    private val imagePickerLauncher: ActivityResultLauncher<String>
) {

    @JavascriptInterface
    fun getData(): String = dataStore.getData()

    @JavascriptInterface
    fun saveData(json: String) {
        dataStore.saveData(json)
    }

    @JavascriptInterface
    fun openUrl(url: String) {
        activity.runOnUiThread {
            activity.showBrowser(normalizeUrl(url))
        }
    }

    @JavascriptInterface
    fun goHome() {
        activity.runOnUiThread {
            activity.showHome()
        }
    }

    @JavascriptInterface
    fun navigateInBrowser(url: String) {
        activity.runOnUiThread {
            activity.showBrowser(normalizeUrl(url))
        }
    }

    @JavascriptInterface
    fun pickImageWithCallback() {
        activity.runOnUiThread {
            activity.pendingImageCallback = true
            imagePickerLauncher.launch("image/*")
        }
    }

    @JavascriptInterface
    fun browserGoBack() {
        activity.runOnUiThread {
            activity.browserGoBack()
        }
    }

    @JavascriptInterface
    fun browserGoForward() {
        activity.runOnUiThread {
            activity.browserGoForward()
        }
    }

    fun deliverImageResult(uri: Uri?) {
        if (uri == null) {
            invokeImageCallback("")
            return
        }
        try {
            val bytes = activity.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            if (bytes == null) {
                invokeImageCallback("")
                return
            }
            val mime = activity.contentResolver.getType(uri) ?: "image/jpeg"
            val base64 = Base64.encodeToString(bytes, Base64.NO_WRAP)
            invokeImageCallback("data:$mime;base64,$base64")
        } catch (_: Exception) {
            invokeImageCallback("")
        }
    }

    private fun invokeImageCallback(dataUrl: String) {
        val webView = activity.getBridgeWebView() ?: return
        val escaped = dataUrl.replace("\\", "\\\\").replace("'", "\\'")
        webView.post {
            webView.evaluateJavascript(
                "window.__novaImageCallback && window.__novaImageCallback('$escaped');",
                null
            )
        }
    }

    private fun normalizeUrl(input: String): String {
        val trimmed = input.trim()
        if (trimmed.isEmpty()) return trimmed
        if (trimmed.startsWith("http://", true) || trimmed.startsWith("https://", true)) {
            return trimmed
        }
        if (trimmed.contains(".") && !trimmed.contains(" ")) {
            return "https://$trimmed"
        }
        return activity.searchUrlFor(trimmed)
    }
}
