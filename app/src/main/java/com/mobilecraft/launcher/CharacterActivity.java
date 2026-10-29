package com.mobilecraft.launcher;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.GridView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Character (skin) and model (classic / slim) selection screen. */
public class CharacterActivity extends Activity {

    private static final int REQUEST_SKIN = 1;

    private Prefs prefs;
    private String selectedId;
    private boolean slim;

    private SkinView preview;
    private TextView previewName;
    private Button modelClassic, modelSlim;
    private final List<String> ids = new ArrayList<>();
    private final Map<String, Bitmap> cache = new HashMap<>();
    private CharacterAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_character);
        prefs = new Prefs(this);
        selectedId = prefs.characterId();
        slim = prefs.isSlim();

        preview = findViewById(R.id.preview);
        previewName = findViewById(R.id.preview_name);
        modelClassic = findViewById(R.id.model_classic);
        modelSlim = findViewById(R.id.model_slim);
        preview.enableTurnOnTap();

        reloadIds();
        GridView grid = findViewById(R.id.grid);
        adapter = new CharacterAdapter();
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, position, id) -> {
            selectedId = ids.get(position);
            if (!Character.CUSTOM_ID.equals(selectedId)) {
                slim = Character.find(Character.builtIn(), selectedId).slimByDefault;
            }
            refresh();
        });

        modelClassic.setOnClickListener(v -> { slim = false; refresh(); });
        modelSlim.setOnClickListener(v -> { slim = true; refresh(); });

        findViewById(R.id.btn_import).setOnClickListener(v -> {
            Intent i = new Intent(Intent.ACTION_GET_CONTENT);
            i.setType("image/png");
            i.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(Intent.createChooser(i, "Выберите скин Minecraft (PNG)"), REQUEST_SKIN);
        });

        findViewById(R.id.btn_save).setOnClickListener(v -> {
            prefs.setCharacterId(selectedId);
            prefs.setModel(slim ? Prefs.MODEL_SLIM : Prefs.MODEL_CLASSIC);
            finish();
        });

        refresh();
    }

    private void reloadIds() {
        ids.clear();
        for (Character c : Character.builtIn()) ids.add(c.id);
        if (prefs.customSkinFile().exists()) ids.add(Character.CUSTOM_ID);
    }

    private Bitmap skin(String id) {
        // Built-in skins are generated per model; the custom skin is the same file for both.
        String key = Character.CUSTOM_ID.equals(id) ? id : id + (slim ? ":slim" : ":classic");
        Bitmap b = cache.get(key);
        if (b == null) {
            b = prefs.skinFor(id, slim);
            cache.put(key, b);
        }
        return b;
    }

    private void refresh() {
        preview.setSkin(skin(selectedId), slim);
        previewName.setText(prefs.characterName(selectedId));
        modelClassic.setBackgroundResource(slim ? R.drawable.btn_secondary : R.drawable.card_selected);
        modelSlim.setBackgroundResource(slim ? R.drawable.card_selected : R.drawable.btn_secondary);
        adapter.notifyDataSetChanged();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_SKIN || resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        try (InputStream in = getContentResolver().openInputStream(data.getData())) {
            Bitmap bmp = BitmapFactory.decodeStream(in);
            if (bmp == null || bmp.getWidth() != 64 || (bmp.getHeight() != 64 && bmp.getHeight() != 32)) {
                Toast.makeText(this, "Нужен PNG-скин размером 64×64 или 64×32", Toast.LENGTH_LONG).show();
                return;
            }
            try (FileOutputStream out = new FileOutputStream(prefs.customSkinFile())) {
                bmp.compress(Bitmap.CompressFormat.PNG, 100, out);
            }
            cache.remove(Character.CUSTOM_ID);
            reloadIds();
            selectedId = Character.CUSTOM_ID;
            refresh();
            Toast.makeText(this, "Скин загружен. Выберите модель: классическая или тонкая.",
                    Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Не удалось загрузить скин: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private final class CharacterAdapter extends BaseAdapter {
        @Override public int getCount() { return ids.size(); }
        @Override public Object getItem(int position) { return ids.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            View v = convertView != null ? convertView
                    : getLayoutInflater().inflate(R.layout.item_character, parent, false);
            String id = ids.get(position);
            SkinView sv = v.findViewById(R.id.skin);
            TextView name = v.findViewById(R.id.name);
            sv.setSkin(skin(id), slim);
            name.setText(prefs.characterName(id));
            v.setBackgroundResource(id.equals(selectedId) ? R.drawable.card_selected : R.drawable.panel);
            return v;
        }
    }
}
