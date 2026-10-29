package com.mobilecraft.launcher;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** An entry of Mojang's version manifest. */
public final class GameVersion {

    public static final String MANIFEST_URL =
            "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json";

    public final String id;
    public final String type;        // release, snapshot, old_beta, old_alpha
    public final String url;         // version JSON url, null for the offline list
    public final String releaseTime;

    GameVersion(String id, String type, String url, String releaseTime) {
        this.id = id;
        this.type = type;
        this.url = url;
        this.releaseTime = releaseTime;
    }

    public boolean isRelease() { return "release".equals(type); }
    public boolean isSnapshot() { return "snapshot".equals(type); }
    public boolean isOld() { return type.startsWith("old_"); }

    public String typeLabel() {
        switch (type) {
            case "release": return "Релиз";
            case "snapshot": return "Снапшот";
            case "old_beta": return "Бета";
            case "old_alpha": return "Альфа";
            default: return type;
        }
    }

    static List<GameVersion> parseManifest(String json) throws JSONException {
        JSONArray arr = new JSONObject(json).getJSONArray("versions");
        List<GameVersion> list = new ArrayList<>(arr.length());
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.getJSONObject(i);
            String time = o.optString("releaseTime", "");
            list.add(new GameVersion(o.getString("id"), o.getString("type"),
                    o.getString("url"), time.length() >= 10 ? time.substring(0, 10) : time));
        }
        return list;
    }

    /** Shown when there is no network and no cached manifest. */
    static List<GameVersion> offlineList() {
        String[] ids = {"1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.19.2",
                "1.18.2", "1.17.1", "1.16.5", "1.12.2", "1.8.9", "1.7.10"};
        List<GameVersion> list = new ArrayList<>();
        for (String id : ids) list.add(new GameVersion(id, "release", null, ""));
        return list;
    }
}
