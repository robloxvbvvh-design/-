package com.mobilecraft.launcher;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.CheckBox;
import android.widget.ListView;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Lists Minecraft: Java Edition versions from Mojang's manifest. */
public class VersionActivity extends Activity {

    private final List<GameVersion> all = new ArrayList<>();
    private final List<GameVersion> shown = new ArrayList<>();
    private CheckBox fRelease, fSnapshot, fOld;
    private TextView statusView;
    private VersionAdapter adapter;
    private Prefs prefs;
    private File gameDir;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_version);
        prefs = new Prefs(this);
        File base = getExternalFilesDir(null);
        gameDir = new File(base != null ? base : getFilesDir(), ".minecraft");

        fRelease = findViewById(R.id.f_release);
        fSnapshot = findViewById(R.id.f_snapshot);
        fOld = findViewById(R.id.f_old);
        statusView = findViewById(R.id.v_status);
        ListView list = findViewById(R.id.list);
        adapter = new VersionAdapter();
        list.setAdapter(adapter);
        list.setOnItemClickListener((p, v, position, id) -> {
            prefs.setVersion(shown.get(position).id);
            finish();
        });

        fRelease.setOnCheckedChangeListener((b, c) -> applyFilter());
        fSnapshot.setOnCheckedChangeListener((b, c) -> applyFilter());
        fOld.setOnCheckedChangeListener((b, c) -> applyFilter());

        loadVersions();
    }

    private void loadVersions() {
        final File cacheFile = new File(getFilesDir(), "version_manifest.json");
        new Thread(() -> {
            List<GameVersion> result;
            String note = null;
            try {
                String json = Http.getString(GameVersion.MANIFEST_URL);
                result = GameVersion.parseManifest(json);
                try (FileOutputStream out = new FileOutputStream(cacheFile)) {
                    out.write(json.getBytes(StandardCharsets.UTF_8));
                }
            } catch (Exception e) {
                try {
                    result = GameVersion.parseManifest(GameInstaller.readFile(cacheFile));
                    note = "Нет сети — показан сохранённый список";
                } catch (Exception e2) {
                    result = GameVersion.offlineList();
                    note = getString(R.string.offline_list);
                }
            }
            final List<GameVersion> r = result;
            final String n = note;
            runOnUiThread(() -> {
                all.clear();
                all.addAll(r);
                statusView.setText(n);
                statusView.setVisibility(n == null ? View.GONE : View.VISIBLE);
                applyFilter();
            });
        }, "version-list").start();
    }

    private void applyFilter() {
        shown.clear();
        for (GameVersion v : all) {
            if ((v.isRelease() && fRelease.isChecked())
                    || (v.isSnapshot() && fSnapshot.isChecked())
                    || (v.isOld() && fOld.isChecked())) {
                shown.add(v);
            }
        }
        adapter.notifyDataSetChanged();
    }

    private final class VersionAdapter extends BaseAdapter {
        @Override public int getCount() { return shown.size(); }
        @Override public Object getItem(int position) { return shown.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView
                    : getLayoutInflater().inflate(R.layout.item_version, parent, false);
            GameVersion gv = shown.get(position);
            TextView id = v.findViewById(R.id.v_id);
            TextView info = v.findViewById(R.id.v_info);
            id.setText(gv.id);
            StringBuilder sb = new StringBuilder(gv.typeLabel());
            if (!gv.releaseTime.isEmpty()) sb.append(" · ").append(gv.releaseTime);
            if (GameInstaller.isInstalled(gameDir, gv.id)) sb.append(" · ").append(getString(R.string.installed));
            info.setText(sb);
            boolean selected = gv.id.equals(prefs.version());
            v.setBackgroundResource(selected ? R.drawable.card_selected : R.drawable.panel);
            return v;
        }
    }
}
