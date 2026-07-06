"""Central definitions for AI card styles and social image sizes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CardStyle:
    code: str
    name: str
    description: str
    visual_prompt: str
    layout: str
    typography: str
    palette: str


@dataclass(frozen=True, slots=True)
class CardSize:
    code: str
    name: str
    api_size: str


CARD_STYLES = {
    "minimal": CardStyle(
        "minimal",
        "藝廊語錄海報",
        "現代藝廊留白、抽象主視覺。",
        "現代藝廊牆上的文字海報，一處抽象主視覺與大量乾淨留白",
        "標題如展覽標示置頂，金句成為畫面主角，重點收在下緣",
        "精緻無襯線；標題極大、資訊字極小，留白形成節奏",
        "主色暖白與石灰，輔色霧藍，柔和自然光，明暗乾淨克制",
    ),
    "vibrant": CardStyle(
        "vibrant",
        "日漫唯美海報",
        "天空、花瓣、城市燈火的浪漫場景。",
        "日系動畫電影的浪漫場景感：天空、花瓣、城市燈火或季節物件；唯美而非幼態",
        "標題融入天空或景物的平靜區，金句像電影宣傳文案，重點化為小型資訊區",
        "優雅日系海報字感；大標有情緒、金句細緻、資訊字乾淨",
        "晚霞粉橘、鈷藍、紫羅蘭與金色微光；明亮但漸層和諧",
    ),
    "magazine": CardStyle(
        "magazine",
        "文藝雜誌封面",
        "文化雜誌封面與象徵性主視覺。",
        "文學季刊或高級文化雜誌，搭配象徵文章主題的攝影或插畫主視覺",
        "像專欄封面；大金句壓在主視覺留白處，資訊欄沿側邊排列",
        "優雅襯線大標配無襯線資訊字，明確字級對比",
        "象牙白、炭黑，加一個深寶石色；棚拍般的對比光",
    ),
    "dark": CardStyle(
        "dark",
        "賽博龐克夜景",
        "雨夜城市、玻璃反射與資料介面。",
        "雨夜城市、發光招牌、玻璃反射、未來感資料介面；精緻電影感而非廉價霓虹",
        "中央主標如全息介面，重點以細線資料窗環繞",
        "幾何無襯線、寬字距、微光邊緣，保持清楚可讀",
        "近黑藏青、靛紫、電光青與少量洋紅；暗底上的受控高對比",
    ),
    "handwritten": CardStyle(
        "handwritten",
        "手寫情書",
        "信紙、鋼筆墨跡與乾燥花。",
        "信紙、鋼筆墨跡、乾燥花或郵票、柔和日光；像被珍藏的私人書信",
        "金句是信紙中央的主段落，重點以邊註或手寫條列呈現",
        "自然鋼筆手寫感標題，正文為清楚的印刷小字",
        "奶油紙、墨藍、褪色玫瑰粉；溫暖側光",
    ),
    "notebook": CardStyle(
        "notebook",
        "螺旋筆記本",
        "方格紙、螺旋孔、便條貼與紙膠帶。",
        "橫線或方格紙、左側螺旋孔、便條貼與紙膠帶",
        "保留筆記本邊界；標題像章節名，重點寫在格線中",
        "圓潤手寫標題，正文為乾淨易讀的筆記字感",
        "淡紙色、霧藍格線、柔和粉彩便條",
    ),
    "sticky_notes": CardStyle(
        "sticky_notes",
        "便利貼拼貼",
        "便利貼陰影與撕貼邊緣。",
        "便利貼帶柔和陰影與撕貼邊緣",
        "金句是一張主便利貼，2到4個重點分散在小便條",
        "粗麥克筆標題、短句手寫感，避免密集小字",
        "去飽和奶油黃、霧粉、粉藍，襯中性底",
    ),
    "newspaper": CardStyle(
        "newspaper",
        "報紙剪報",
        "米黃新聞紙、網點與剪報邊。",
        "米黃新聞紙、網點、剪報邊",
        "多欄網格與剪報標籤，金句像頭條",
        "粗襯線頭條字、窄欄正文、明確欄位層級",
        "做舊奶油紙、柔黑墨、一抹褪色磚紅，低彩度",
    ),
    "bento": CardStyle(
        "bento",
        "日系資訊便當盒",
        "圓角資訊格與平靜秩序。",
        "像設計精良的 App 介面：圓角資訊格、可愛小圖示、平靜秩序",
        "標題在上方，2到4個重點各自收進均衡資訊格",
        "圓角無襯線；標題粗、格內重點短且整齊",
        "燕麥、鼠尾草綠、赤陶、霧天藍；明亮柔和、不黏膩",
    ),
    "retro_print": CardStyle(
        "retro_print",
        "復古旅行海報",
        "Riso 疊色與象徵性山海城市。",
        "絲網印刷或 Riso 疊色、紙張顆粒、象徵性的山海、城市或交通主視覺",
        "大字與插畫留白並置，像一張值得收藏的旅行海報",
        "粗襯線或木刻字感標題，重點簡潔、字級對比大",
        "赭黃、旅人藍、磚紅襯暖紙；可飽和但有復古套印感",
    ),
    "blueprint": CardStyle(
        "blueprint",
        "藍圖筆記",
        "工程格線、白色細線與註記箭頭。",
        "藍圖深底、白色細線、工程格線、註記箭頭",
        "金句為主模組，重點以標註框與連線整理",
        "等寬或技術製圖字感，標題與註記層級分明",
        "深藏青到青底、白與淡青線，單色系",
    ),
    "ink_wash": CardStyle(
        "ink_wash",
        "水墨箋紙",
        "宣紙、淡墨暈染、留白與印章色。",
        "宣紙、淡墨暈染、留白與一處低彩度印章色",
        "右上標題、中央金句、下方簡短條列，留白充足",
        "優雅書寫感標題搭配乾淨印刷小字，不要求書法字可辨識",
        "宣紙米、灰墨漸層、一抹霧朱砂",
    ),
    "storybook": CardStyle(
        "storybook",
        "童書繪本",
        "手繪水彩或色鉛筆隱喻物件。",
        "手繪水彩或色鉛筆插畫，以小屋、植物、雲朵等物件隱喻文章主題",
        "標題像繪本書名，金句置於插畫留白，重點如頁腳小註",
        "圓潤手寫感書名搭配清楚的印刷小字",
        "奶油黃、天空藍、草木綠、珊瑚粉；柔亮晨光",
    ),
    "tarot": CardStyle(
        "tarot",
        "星象塔羅卡",
        "月相、星圖、植物與金色線框。",
        "深色紙卡、月相、星圖、植物與金色線框；神祕但優雅",
        "金句置中如牌面核心，重點收在下方飾框或側邊小標籤",
        "古典襯線標題、細緻小型大寫字感、華麗但不難讀",
        "午夜藍、墨紫、古金、月白；高對比的微光",
    ),
}

CARD_SIZES = {
    "ig_post": CardSize("ig_post", "IG 貼文（1:1）", "1024x1024"),
    "ig_story": CardSize("ig_story", "IG 限動（9:16）", "1024x1536"),
    "fb_portrait": CardSize("fb_portrait", "FB 直式貼文（4:5）", "1024x1536"),
    "fb_landscape": CardSize("fb_landscape", "FB 橫式貼文（16:9）", "1536x1024"),
}

DEFAULT_STYLE = "minimal"
DEFAULT_SIZE = "ig_post"


def get_style(code: str | None) -> CardStyle:
    return CARD_STYLES.get(code or "", CARD_STYLES[DEFAULT_STYLE])


def get_size(code: str | None) -> CardSize:
    return CARD_SIZES.get(code or "", CARD_SIZES[DEFAULT_SIZE])
