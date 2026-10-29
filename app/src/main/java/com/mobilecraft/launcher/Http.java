package com.mobilecraft.launcher;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Minimal blocking HTTP helpers; call them off the UI thread. */
final class Http {

    private Http() {}

    static String getString(String url) throws IOException {
        HttpURLConnection conn = open(url);
        try (InputStream in = conn.getInputStream()) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            copy(in, out);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } finally {
            conn.disconnect();
        }
    }

    /** Downloads to {@code dest} via a temporary file, so partial downloads never look complete. */
    static void download(String url, File dest) throws IOException {
        File parent = dest.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("Не удалось создать папку " + parent);
        }
        File tmp = new File(dest.getPath() + ".part");
        HttpURLConnection conn = open(url);
        try (InputStream in = conn.getInputStream(); OutputStream out = new FileOutputStream(tmp)) {
            copy(in, out);
        } finally {
            conn.disconnect();
        }
        if (dest.exists()) dest.delete();
        if (!tmp.renameTo(dest)) throw new IOException("Не удалось сохранить " + dest);
    }

    private static HttpURLConnection open(String url) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(30000);
        conn.setRequestProperty("User-Agent", "MobileCraftLauncher/1.0");
        int code = conn.getResponseCode();
        if (code != HttpURLConnection.HTTP_OK) {
            conn.disconnect();
            throw new IOException("HTTP " + code + " для " + url);
        }
        return conn;
    }

    private static void copy(InputStream in, OutputStream out) throws IOException {
        byte[] buf = new byte[16384];
        int n;
        while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
    }
}
