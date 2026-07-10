package com.nova.browser

import android.annotation.SuppressLint
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageButton
import android.widget.LinearLayout
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var tabManager: TabManager
    private lateinit var pageContainer: FrameLayout
    private lateinit var urlInput: EditText
    private lateinit var btnStar: ImageButton
    private lateinit var btnBack: ImageButton
    private lateinit var btnForward: ImageButton
    private lateinit var dataStore: DataStore
    private lateinit var novaBridge: NovaBridge

    var pendingImageCallback = false

    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: android.net.Uri? ->
        novaBridge.deliverImageResult(uri)
        pendingImageCallback = false
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.parseColor("#1a1a2e")
        setContentView(R.layout.activity_main)

        val rootLayout = findViewById<FrameLayout>(R.id.rootLayout)
        ViewCompat.setOnApplyWindowInsetsListener(rootLayout) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        ViewCompat.requestApplyInsets(rootLayout)

        dataStore = DataStore(this)
        pageContainer = findViewById(R.id.pageContainer)
        val tabStrip = findViewById<LinearLayout>(R.id.tabStrip)
        val tabStripScroll = findViewById<HorizontalScrollView>(R.id.tabStripScroll)
        urlInput = findViewById(R.id.urlInput)
        btnStar = findViewById(R.id.btnStar)
        btnBack = findViewById(R.id.btnBack)
        btnForward = findViewById(R.id.btnForward)

        tabManager = TabManager(
            this,
            pageContainer,
            tabStrip,
            tabStripScroll,
            onActiveTabChanged = { onActiveTabChanged() },
            setupWebView = { webView, tab -> setupTabWebView(webView, tab) }
        )

        novaBridge = NovaBridge(this, dataStore, imagePickerLauncher)

        btnBack.setOnClickListener { browserGoBack() }
        btnForward.setOnClickListener { browserGoForward() }
        findViewById<ImageButton>(R.id.btnReload).setOnClickListener { reloadActiveTab() }
        findViewById<ImageButton>(R.id.btnHome).setOnClickListener { tabManager.goHomeInActiveTab() }
        findViewById<ImageButton>(R.id.btnNewTab).setOnClickListener { tabManager.newTab(loadHome = true) }
        btnStar.setOnClickListener { toggleBookmark() }

        urlInput.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_GO || actionId == EditorInfo.IME_ACTION_DONE) {
                tabManager.openUrl(urlInput.text.toString())
                true
            } else {
                false
            }
        }

        if (savedInstanceState == null) {
            tabManager.newTab(loadHome = true)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupTabWebView(webView: WebView, tab: BrowserTab) {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = true
            displayZoomControls = false
            mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
            cacheMode = WebSettings.LOAD_DEFAULT
        }
        webView.setBackgroundColor(Color.parseColor("#0a0a12"))
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean = false

            override fun onPageFinished(view: WebView?, url: String?) {
                if (view == null || url == null) return
                val isHome = url.startsWith("file:///android_asset/")
                val title = if (isHome) "Nova" else (view.title ?: tabManager.titleFromUrl(url))
                tabManager.updateTabMeta(tab.id, title, url, isHome)
                if (tab.id == tabManager.activeTabId) {
                    onActiveTabChanged()
                }
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                if (request?.isForMainFrame == true) {
                    val html = """
                        <html><body style="font-family:sans-serif;text-align:center;padding:40px;background:#1a1a2e;color:#e8e8f0;">
                        <h2>Unable to load page</h2>
                        <p>Check your internet connection and try again.</p>
                        </body></html>
                    """.trimIndent()
                    view?.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
                    tabManager.updateTabMeta(tab.id, "Failed", request.url?.toString() ?: "", false)
                }
            }
        }
    }

    fun loadHomeInTab(tab: BrowserTab) {
        tab.isHome = true
        tab.webView.addJavascriptInterface(novaBridge, "NovaBridge")
        tab.webView.loadUrl("file:///android_asset/ui/index.html")
        tab.title = "Nova"
        tab.url = ""
    }

    fun loadSiteInTab(tab: BrowserTab, url: String) {
        tab.isHome = false
        tab.webView.removeJavascriptInterface("NovaBridge")
        tab.webView.loadUrl(url)
        tab.url = url
    }

    fun showBrowser(url: String, newTab: Boolean = false) {
        tabManager.openUrl(url, newTab = newTab)
    }

    fun showHome() {
        tabManager.goHomeInActiveTab()
    }

    fun getBridgeWebView(): WebView? {
        val tab = tabManager.getActiveTab()
        return if (tab?.isHome == true) tab.webView else null
    }

    private fun onActiveTabChanged() {
        val tab = tabManager.getActiveTab() ?: return
        val webView = tab.webView
        if (tab.isHome) {
            urlInput.setText("")
        } else {
            urlInput.setText(webView.url ?: tab.url)
            updateStarState(webView.url ?: tab.url)
        }
        btnBack.isEnabled = webView.canGoBack() || tabManager.tabs.size > 1
        btnForward.isEnabled = webView.canGoForward()
    }

    private fun reloadActiveTab() {
        val tab = tabManager.getActiveTab() ?: return
        if (tab.isHome) {
            loadHomeInTab(tab)
        } else {
            tab.webView.reload()
        }
    }

    fun browserGoBack() {
        val webView = tabManager.getActiveWebView()
        if (webView != null && webView.canGoBack()) {
            webView.goBack()
            return
        }
        if (tabManager.tabs.size > 1) {
            val active = tabManager.getActiveTab() ?: return
            val index = tabManager.tabs.indexOf(active)
            val prev = tabManager.tabs[(index - 1 + tabManager.tabs.size) % tabManager.tabs.size]
            tabManager.activateTab(prev.id)
        }
    }

    fun browserGoForward() {
        tabManager.getActiveWebView()?.takeIf { it.canGoForward() }?.goForward()
    }

    private fun toggleBookmark() {
        val tab = tabManager.getActiveTab() ?: return
        if (tab.isHome) return
        val url = (tab.webView.url ?: tab.url).trim()
        if (url.isEmpty()) return

        val data = JSONObject(dataStore.getData())
        val bookmarks = data.optJSONArray("bookmarks") ?: JSONArray()
        val normalized = normalizeUrl(url)

        var existingIndex = -1
        for (i in 0 until bookmarks.length()) {
            val item = bookmarks.getJSONObject(i)
            if (normalizeUrl(item.optString("url")) == normalized) {
                existingIndex = i
                break
            }
        }

        if (existingIndex >= 0) {
            val item = bookmarks.getJSONObject(existingIndex)
            item.put("pinned", !item.optBoolean("pinned", false))
        } else {
            val title = tab.webView.title ?: Uri.parse(normalized).host ?: "Bookmark"
            val bookmark = JSONObject()
            bookmark.put("id", "bm-" + System.currentTimeMillis())
            bookmark.put("title", title)
            bookmark.put("url", normalized)
            bookmark.put("pinned", true)
            bookmarks.put(bookmark)
        }

        data.put("bookmarks", bookmarks)
        dataStore.saveData(data.toString())
        updateStarState(normalized)
    }

    private fun updateStarState(url: String) {
        val normalized = normalizeUrl(url)
        val data = JSONObject(dataStore.getData())
        val bookmarks = data.optJSONArray("bookmarks") ?: JSONArray()
        var bookmarked = false
        for (i in 0 until bookmarks.length()) {
            val item = bookmarks.getJSONObject(i)
            if (normalizeUrl(item.optString("url")) == normalized) {
                bookmarked = true
                break
            }
        }
        btnStar.setImageResource(
            if (bookmarked) android.R.drawable.btn_star_big_on
            else android.R.drawable.btn_star_big_off
        )
        btnStar.isEnabled = !normalized.isEmpty()
    }

    fun normalizeUrl(input: String): String {
        val trimmed = input.trim()
        if (trimmed.isEmpty()) return trimmed
        if (trimmed.startsWith("http://", true) || trimmed.startsWith("https://", true)) {
            return trimmed
        }
        if (trimmed.contains(".") && !trimmed.contains(" ")) {
            return "https://$trimmed"
        }
        return searchUrlFor(trimmed)
    }

    fun searchUrlFor(query: String): String {
        val data = JSONObject(dataStore.getData())
        val engine = data.optJSONObject("settings")?.optString("searchEngine", "google") ?: "google"
        val base = when (engine) {
            "duckduckgo" -> "https://duckduckgo.com/?q="
            "bing" -> "https://www.bing.com/search?q="
            "brave" -> "https://search.brave.com/search?q="
            else -> "https://www.google.com/search?q="
        }
        return base + Uri.encode(query)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        val webView = tabManager.getActiveWebView()
        when {
            webView != null && webView.canGoBack() -> webView.goBack()
            tabManager.tabs.size > 1 -> {
                val active = tabManager.getActiveTab()
                if (active != null) tabManager.closeTab(active.id)
            }
            else -> super.onBackPressed()
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            val webView = tabManager.getActiveWebView()
            when {
                webView != null && webView.canGoBack() -> {
                    webView.goBack()
                    return true
                }
                tabManager.tabs.size > 1 -> {
                    tabManager.getActiveTab()?.let { tabManager.closeTab(it.id) }
                    return true
                }
            }
        }
        return super.onKeyDown(keyCode, event)
    }
}
