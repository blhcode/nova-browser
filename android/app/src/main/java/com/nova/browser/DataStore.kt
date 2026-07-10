package com.nova.browser

import android.content.Context
import org.json.JSONObject
import java.io.File

class DataStore(context: Context) {

    private val file = File(context.filesDir, "nova-browser-data.json")

    private val defaultJson = """
        {
          "bookmarks": [],
          "theme": {
            "mode": "space",
            "customBgColor": "#0a0a12",
            "customAccentColor": "#6b8cff",
            "customBgImage": null
          },
          "settings": {
            "searchEngine": "google",
            "homepage": "",
            "javascriptEnabled": true,
            "desktopMode": false,
            "blockThirdPartyCookies": true,
            "zoomLevel": 100
          }
        }
    """.trimIndent()

    @Synchronized
    fun getData(): String {
        if (!file.exists()) {
            file.writeText(defaultJson)
        }
        return file.readText()
    }

    @Synchronized
    fun saveData(json: String) {
        JSONObject(json)
        file.writeText(json)
    }
}
