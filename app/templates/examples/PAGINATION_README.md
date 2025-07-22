# 分页功能修复指南

## 问题
入库操作界面导入的数据超过30条后页面无法完整展示，这是因为缺少分页功能导致的。

## 解决方案

### 1. 导入分页宏
在需要分页的模板顶部添加:
```html
{% from 'macros/pagination.html' import render_pagination %}
```

### 2. 在表格下方添加分页控件
```html
{{ render_pagination(pagination, '路由端点名', **request.args) }}
```
例如，对于入库列表页面:
```html
{{ render_pagination(pagination, 'main.inbound_list', **request.args) }}
```

### 3. 修改路由处理函数
在路由处理函数中添加分页逻辑:
```python
# 获取分页参数
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 30, type=int)

# 构建查询
query = Model.query

# 应用排序
query = query.order_by(Model.created_at.desc())

# 应用分页
pagination = query.paginate(page=page, per_page=per_page, error_out=False)
records = pagination.items

# 渲染模板，传递分页对象
return render_template('template.html', records=records, pagination=pagination)
```

### 4. 修改所有需要分页的页面
- 入库记录列表
- 出库记录列表
- 库存记录列表
- 其他可能包含大量数据的页面

## 注意事项
- 每页默认显示30条记录
- 分页宏会自动处理页码导航
- 分页查询会大大提高页面加载速度
