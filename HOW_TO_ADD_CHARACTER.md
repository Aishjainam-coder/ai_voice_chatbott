# 👤 Apna Character/Photo Kaise Add Karein

## Character Image Add Karne Ke Liye:

### Step 1: Assets Folder Mein Photo Daalo

1. **Folder kholo:** `c:\Users\hp\ai chatbot\assets\`
2. **Photo copy karo** (kisi bhi normal human photo - CEO, friend, ya koi bhi)
3. **Rename karo:** `character.png` (ya `character.jpg`)

**Example:**
```
c:\Users\hp\ai chatbot\assets\character.png
```

### Step 2: Photo Requirements

- **Format:** PNG ya JPG
- **Size:** Koi bhi (automatic resize hoga)
- **Face:** Clear face photo (front-facing best hai)
- **Background:** Koi bhi (transparent PNG bhi chalega)

### Step 3: Restart Karein

1. **Stop karo** chatbot (Ctrl+C in terminal)
2. **Restart karo:** `python ai_chatbot.py`
3. **Refresh karo** browser (F5)

---

## Kya Hoga:

✅ **Tumhari photo dikhegi** character ki jagah  
✅ **Mouth animate hoga** (lip sync) - photo ke upar  
✅ **Emotions dikhenge** badge ke saath  
✅ **Eyes** tumhari photo wali hi rahengi (overlay nahi hoga)

---

## Example Photos:

- CEO photo
- Friend ka photo  
- Koi bhi human face photo
- Even cartoon character photo (agar face clear hai)

**Note:** Photo mein face clear hona chahiye taaki mouth position sahi ho.

---

## Troubleshooting:

**Photo nahi dikh rahi?**
- Check: `assets/character.png` file exists
- File name exactly `character.png` hona chahiye
- Restart chatbot after adding photo

**Mouth position galat?**
- Photo mein face center mein hona chahiye
- Front-facing photo best hai
