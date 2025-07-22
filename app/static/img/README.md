# CFW车夫网标识文件

## 文件说明
- cfw_logo.svg: CFW车夫网标识的SVG矢量图
- 可以在此目录放置您的CFW车夫网标识图片文件

## 支持的图片格式
- PNG (推荐)
- JPG/JPEG
- SVG (矢量图，推荐用于打印)
- GIF

## 使用方法
在HTML模板中使用：
```html
<img src="{{ url_for('static', filename='img/cfw_logo.svg') }}" alt="CFW车夫网" class="cfw-logo">
```

## 建议尺寸
- 宽度: 120-150px
- 高度: 40-50px
- 分辨率: 300DPI (用于打印)
