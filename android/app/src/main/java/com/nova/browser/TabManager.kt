package com.nova.browser

import android.graphics.Color
import android.net.Uri
import android.view.Gravity
import android.view.View
import android.webkit.WebView
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.TextView
import java.util.UUID

data class BrowserTab(
    val id: String,
    val webView: WebView,
    var title: String = "Nova",
    var url: String = "",
    var isHome: Boolean = true,
    var chipView: LinearLayout? = null
)

class TabManager(
    private val activity: MainActivity,
    private val pageContainer: FrameLayout,
    private val tabStrip: LinearLayout,
    private val tabStripScroll: HorizontalScrollView,
    private val onActiveTabChanged: () -> Unit,
    private val setupWebView: (WebView, BrowserTab) -> Unit
) {
    val tabs = mutableListOf<BrowserTab>()
    var activeTabId: String? = null

    fun newTab(loadHome: Boolean = true): BrowserTab {
        val tab = createTab()
        activateTab(tab.id)
        if (loadHome) {
            activity.loadHomeInTab(tab)
        }
        return tab
    }

    fun openUrl(url: String, newTab: Boolean = false): BrowserTab {
        val normalized = activity.normalizeUrl(url)
        if (normalized.isEmpty()) {
            return getActiveTab() ?: newTab(loadHome = true)
        }
        val tab = when {
            newTab -> newTab(loadHome = false)
            tabs.isEmpty() -> newTab(loadHome = false)
            else -> getActiveTab() ?: newTab(loadHome = false)
        }
        activateTab(tab.id)
        activity.loadSiteInTab(tab, normalized)
        return tab
    }

    fun goHomeInActiveTab(): BrowserTab {
        val tab = getActiveTab() ?: newTab(loadHome = true)
        activateTab(tab.id)
        activity.loadHomeInTab(tab)
        return tab
    }

    fun getActiveTab(): BrowserTab? =
        tabs.firstOrNull { it.id == activeTabId }

    fun getActiveWebView(): WebView? = getActiveTab()?.webView

    fun activateTab(tabId: String) {
        if (tabs.none { it.id == tabId }) return
        activeTabId = tabId
        tabs.forEach { tab ->
            val visible = tab.id == tabId
            tab.webView.visibility = if (visible) View.VISIBLE else View.GONE
        }
        rebuildTabStrip()
        onActiveTabChanged()
    }

    fun closeTab(tabId: String) {
        val tab = tabs.firstOrNull { it.id == tabId } ?: return
        val index = tabs.indexOf(tab)
        tabs.remove(tab)
        pageContainer.removeView(tab.webView)
        tab.webView.destroy()

        if (tabs.isEmpty()) {
            newTab(loadHome = true)
            return
        }

        if (activeTabId == tabId) {
            val nextIndex = index.coerceAtMost(tabs.lastIndex)
            activateTab(tabs[nextIndex].id)
        } else {
            rebuildTabStrip()
        }
    }

    fun updateTabMeta(tabId: String, title: String, url: String, isHome: Boolean) {
        val tab = tabs.firstOrNull { it.id == tabId } ?: return
        tab.title = title
        tab.url = url
        tab.isHome = isHome
        tab.chipView?.findViewWithTag<TextView>("tab_title")?.text = title
        if (tabId == activeTabId) {
            onActiveTabChanged()
        }
    }

    private fun createTab(): BrowserTab {
        val tabId = UUID.randomUUID().toString()
        val webView = WebView(activity).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            visibility = View.GONE
        }
        val tab = BrowserTab(id = tabId, webView = webView)
        setupWebView(webView, tab)
        tabs.add(tab)
        pageContainer.addView(webView)
        rebuildTabStrip()
        return tab
    }

    private fun rebuildTabStrip() {
        tabStrip.removeAllViews()
        tabs.forEach { tab ->
            tabStrip.addView(buildTabChip(tab))
        }
    }

    private fun buildTabChip(tab: BrowserTab): LinearLayout {
        val row = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            val active = tab.id == activeTabId
            setBackgroundResource(
                if (active) R.drawable.tab_chip_active_bg else R.drawable.tab_chip_bg
            )
            val pad = (8 * activity.resources.displayMetrics.density).toInt()
            setPadding(pad, pad / 2, pad / 2, pad / 2)
            val margin = (4 * activity.resources.displayMetrics.density).toInt()
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                marginEnd = margin
            }
            setOnClickListener { activateTab(tab.id) }
        }

        val titleView = TextView(activity).apply {
            tag = "tab_title"
            text = tab.title
            setTextColor(Color.parseColor(if (tab.id == activeTabId) "#ffffff" else "#e8e8f2"))
            textSize = 13f
            maxLines = 1
            maxWidth = (140 * activity.resources.displayMetrics.density).toInt()
        }
        row.addView(titleView)

        val close = ImageButton(activity).apply {
            setImageResource(android.R.drawable.ic_menu_close_clear_cancel)
            setBackgroundColor(Color.TRANSPARENT)
            contentDescription = activity.getString(R.string.close_tab)
            val size = (32 * activity.resources.displayMetrics.density).toInt()
            layoutParams = LinearLayout.LayoutParams(size, size)
            setColorFilter(Color.parseColor("#ccccdd"))
            setOnClickListener {
                if (tabs.size > 1) {
                    closeTab(tab.id)
                } else {
                    activity.loadHomeInTab(tab)
                }
            }
        }
        row.addView(close)
        tab.chipView = row
        return row
    }

    fun titleFromUrl(url: String): String {
        return try {
            val host = Uri.parse(url).host
            host?.take(48) ?: url.take(32).ifEmpty { "Page" }
        } catch (_: Exception) {
            url.take(32).ifEmpty { "Page" }
        }
    }
}
