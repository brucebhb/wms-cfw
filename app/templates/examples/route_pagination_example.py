
# 入库记录分页查询示例
@bp.route('/inbound', methods=['GET', 'POST'])
@login_required
def inbound_list():
    form = SearchForm()
    
    if form.validate_on_submit():
        # 处理搜索表单...
        pass
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    
    # 构建查询
    query = InboundRecord.query
    
    # 应用筛选条件
    # ...
    
    # 应用排序
    query = query.order_by(InboundRecord.inbound_time.desc())
    
    # 应用分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items
    
    # 渲染模板，传递分页对象
    return render_template('inbound/list.html', 
                          records=records, 
                          form=form, 
                          pagination=pagination)
