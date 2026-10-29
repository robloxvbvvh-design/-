package com.mobilecraft.launcher;

import java.util.ArrayList;
import java.util.List;

/** A built-in character: a set of colors from which a 64x64 skin is generated. */
public final class Character {

    public static final String CUSTOM_ID = "custom";

    public final String id;
    public final String name;
    public final boolean slimByDefault;
    final int skin, hair, eyes, shirt, shirtDetail, pants, shoes;
    /** Hair style: 0 = short, 1 = long (to shoulders), 2 = bald/helmet. */
    final int hairStyle;

    Character(String id, String name, boolean slim, int hairStyle,
              int skin, int hair, int eyes, int shirt, int shirtDetail, int pants, int shoes) {
        this.id = id;
        this.name = name;
        this.slimByDefault = slim;
        this.hairStyle = hairStyle;
        this.skin = skin;
        this.hair = hair;
        this.eyes = eyes;
        this.shirt = shirt;
        this.shirtDetail = shirtDetail;
        this.pants = pants;
        this.shoes = shoes;
    }

    public static List<Character> builtIn() {
        List<Character> list = new ArrayList<>();
        list.add(new Character("steve", "Стив", false, 0,
                0xFFB78A6E, 0xFF3B2A1E, 0xFF4A3FA8, 0xFF2FA6B5, 0xFF268894, 0xFF3A3592, 0xFF5B5B5B));
        list.add(new Character("alex", "Алекс", true, 1,
                0xFFF2C9A0, 0xFFD9792A, 0xFF3A8A3A, 0xFF6FA84A, 0xFF4F7F33, 0xFF6B4A2B, 0xFF4A3424));
        list.add(new Character("knight", "Рыцарь", false, 2,
                0xFFE0B48F, 0xFFA9A9B4, 0xFF2B2B2B, 0xFF8E8E99, 0xFFC4C4CF, 0xFF6B6B75, 0xFF3D3D45));
        list.add(new Character("miner", "Шахтёр", false, 0,
                0xFFC69676, 0xFF1F1F1F, 0xFF3A2A1A, 0xFFD48A1E, 0xFFF0C040, 0xFF2D3E66, 0xFF2A2A2A));
        list.add(new Character("mage", "Маг", true, 1,
                0xFFF5D5B8, 0xFFE8E8F0, 0xFF6A3AC8, 0xFF5A2D9C, 0xFFE0B83A, 0xFF3E1F6E, 0xFF2A1A40));
        list.add(new Character("ninja", "Ниндзя", true, 2,
                0xFFD9A982, 0xFF141418, 0xFFC02020, 0xFF1E1E24, 0xFFB02828, 0xFF1A1A1F, 0xFF101012));
        list.add(new Character("farmer", "Фермер", false, 0,
                0xFFBF8F6A, 0xFFE0C060, 0xFF2E5FA8, 0xFFB03A2E, 0xFF7A2A20, 0xFF3F5BA0, 0xFF5A3A20));
        list.add(new Character("ice", "Ледяная", true, 1,
                0xFFF0E0DA, 0xFF9ED8F0, 0xFF3AA0D8, 0xFFDDF2FF, 0xFF7CC6F0, 0xFF5A8FC0, 0xFFFFFFFF));
        return list;
    }

    public static Character find(List<Character> list, String id) {
        for (Character c : list) {
            if (c.id.equals(id)) return c;
        }
        return list.get(0);
    }
}
