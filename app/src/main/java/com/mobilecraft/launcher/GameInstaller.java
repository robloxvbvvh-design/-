package com.mobilecraft.launcher;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * Downloads a vanilla Minecraft: Java Edition version (version JSON, client jar,
 * libraries and assets) from Mojang's servers into a .minecraft-style directory.
 */
public final class GameInstaller {

    public interface Listener {
        void onProgress(String message, int done, int total);
        void onFinished(File versionJson);
        void onError(Exception e);
    }

    private static final String ASSETS_URL = "https://resources.download.minecraft.net/";

    private final File gameDir;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private volatile boolean cancelled;

    public GameInstaller(File gameDir) {
        this.gameDir = gameDir;
    }

    public static File versionJson(File gameDir, String id) {
        return new File(gameDir, "versions/" + id + "/" + id + ".json");
    }

    public static File clientJar(File gameDir, String id) {
        return new File(gameDir, "versions/" + id + "/" + id + ".jar");
    }

    public static boolean isInstalled(File gameDir, String id) {
        return new File(gameDir, "versions/" + id + "/.complete").exists();
    }

    public void cancel() {
        cancelled = true;
    }

    public void install(final String versionId, final Listener listener) {
        new Thread(() -> {
            try {
                File json = run(versionId, listener);
                ui.post(() -> listener.onFinished(json));
            } catch (Exception e) {
                ui.post(() -> listener.onError(e));
            }
        }, "game-installer").start();
    }

    private File run(String id, Listener l) throws Exception {
        // 1. Version JSON.
        progress(l, "Поиск версии " + id + "…", 0, 1);
        File jsonFile = versionJson(gameDir, id);
        if (!jsonFile.exists()) {
            String url = findVersionUrl(id);
            Http.download(url, jsonFile);
        }
        JSONObject version = new JSONObject(readFile(jsonFile));

        // 2. Client jar.
        checkCancelled();
        progress(l, "Загрузка клиента " + id + "…", 0, 1);
        JSONObject client = version.getJSONObject("downloads").getJSONObject("client");
        File jar = clientJar(gameDir, id);
        if (!isComplete(jar, client.optLong("size", -1))) {
            Http.download(client.getString("url"), jar);
        }

        // 3. Libraries.
        List<JSONObject> libs = new ArrayList<>();
        JSONArray arr = version.optJSONArray("libraries");
        if (arr != null) {
            for (int i = 0; i < arr.length(); i++) {
                JSONObject lib = arr.getJSONObject(i);
                if (!rulesAllow(lib.optJSONArray("rules"))) continue;
                JSONObject dl = lib.optJSONObject("downloads");
                if (dl != null && dl.optJSONObject("artifact") != null) libs.add(dl.getJSONObject("artifact"));
            }
        }
        for (int i = 0; i < libs.size(); i++) {
            checkCancelled();
            JSONObject a = libs.get(i);
            progress(l, "Библиотеки", i, libs.size());
            File f = new File(gameDir, "libraries/" + a.getString("path"));
            if (!isComplete(f, a.optLong("size", -1))) Http.download(a.getString("url"), f);
        }

        // 4. Assets.
        JSONObject assetIndex = version.optJSONObject("assetIndex");
        if (assetIndex != null) {
            File indexFile = new File(gameDir, "assets/indexes/" + assetIndex.getString("id") + ".json");
            if (!isComplete(indexFile, assetIndex.optLong("size", -1))) {
                Http.download(assetIndex.getString("url"), indexFile);
            }
            JSONObject objects = new JSONObject(readFile(indexFile)).getJSONObject("objects");
            int total = objects.length(), done = 0;
            Iterator<String> keys = objects.keys();
            while (keys.hasNext()) {
                checkCancelled();
                JSONObject o = objects.getJSONObject(keys.next());
                String hash = o.getString("hash");
                String sub = hash.substring(0, 2) + "/" + hash;
                File f = new File(gameDir, "assets/objects/" + sub);
                if (!isComplete(f, o.optLong("size", -1))) Http.download(ASSETS_URL + sub, f);
                if (++done % 25 == 0 || done == total) progress(l, "Ресурсы", done, total);
            }
        }

        new File(gameDir, "versions/" + id + "/.complete").createNewFile();
        return jsonFile;
    }

    private String findVersionUrl(String id) throws Exception {
        for (GameVersion v : GameVersion.parseManifest(Http.getString(GameVersion.MANIFEST_URL))) {
            if (v.id.equals(id)) return v.url;
        }
        throw new IOException("Версия " + id + " не найдена");
    }

    /** Evaluates Mojang library rules for Android (which counts as Linux). */
    static boolean rulesAllow(JSONArray rules) {
        if (rules == null || rules.length() == 0) return true;
        boolean allowed = false;
        for (int i = 0; i < rules.length(); i++) {
            JSONObject rule = rules.optJSONObject(i);
            if (rule == null || rule.has("features")) continue;
            JSONObject os = rule.optJSONObject("os");
            if (os != null && !"linux".equals(os.optString("name", "linux"))) continue;
            allowed = "allow".equals(rule.optString("action"));
        }
        return allowed;
    }

    private static boolean isComplete(File f, long size) {
        return f.exists() && (size < 0 || f.length() == size);
    }

    static String readFile(File f) throws IOException {
        try (FileInputStream in = new FileInputStream(f)) {
            byte[] data = new byte[(int) f.length()];
            int off = 0, n;
            while (off < data.length && (n = in.read(data, off, data.length - off)) > 0) off += n;
            return new String(data, 0, off, StandardCharsets.UTF_8);
        }
    }

    private void checkCancelled() throws InterruptedException {
        if (cancelled) throw new InterruptedException("Отменено");
    }

    private void progress(Listener l, String msg, int done, int total) {
        ui.post(() -> l.onProgress(msg, done, total));
    }
}
