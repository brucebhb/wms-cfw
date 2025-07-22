from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, DateTimeField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from datetime import datetime

def validate_pallet_package_count(form, field):
    """验证件数和板数不能同时为空"""
    # 如果当前字段是板数，检查件数是否也为空
    if field.name == 'pallet_count' and (field.data is None or field.data == 0):
        if form.package_count.data is None or form.package_count.data == 0:
            raise ValidationError('板数和件数不能同时为空')
    # 如果当前字段是件数，检查板数是否也为空
    elif field.name == 'package_count' and (field.data is None or field.data == 0):
        if form.pallet_count.data is None or form.pallet_count.data == 0:
            raise ValidationError('板数和件数不能同时为空')

class InboundRecordForm(FlaskForm):
    """入库记录表单"""
    inbound_time = DateTimeField('入仓时间', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(message='入仓时间不能为空')])
    plate_number = StringField('入仓车牌', validators=[DataRequired(message='入仓车牌不能为空')])
    customer_name = StringField('客户名称', validators=[DataRequired(message='客户名称不能为空')])
    identification_code = StringField('识别编码', render_kw={'readonly': True})
    pallet_count = IntegerField('板数', validators=[NumberRange(min=0, message='板数必须为正数'), validate_pallet_package_count])
    package_count = IntegerField('件数', validators=[NumberRange(min=0, message='件数必须为正数'), validate_pallet_package_count])
    weight = FloatField('重量(kg)', validators=[Optional(), NumberRange(min=0, message='重量必须为正数')])
    volume = FloatField('体积(m³)', validators=[Optional(), NumberRange(min=0, message='体积必须为正数')])
    order_type = SelectField('订单类型', choices=[
        ('', '请选择订单类型'),
        ('原车出境', '原车出境'),
        ('换车出境', '换车出境'),
        ('零担', '零担'),
        ('TP订单', 'TP订单')
    ], validators=[Optional()])
    export_mode = SelectField('出境模式', choices=[
        ('', '请选择出境模式'),
        ('保税', '保税'),
        ('清关', '清关')
    ], validators=[Optional()])
    customs_broker = StringField('报关行', validators=[Optional()])
    location = StringField('库位', validators=[Optional()])
    documents = StringField('单据', validators=[Optional()])
    service_staff = StringField('跟单客服', validators=[DataRequired(message='跟单客服不能为空')])
    submit = SubmitField('提交') 

class InboundRecordEditForm2(FlaskForm):
    """入库记录编辑表单"""
    inbound_time = DateTimeField('入仓时间', format='%Y-%m-%d', validators=[DataRequired(message='入仓时间不能为空')])
    plate_number = StringField('入仓车牌', validators=[DataRequired(message='入仓车牌不能为空')])
    customer_name = StringField('客户名称', validators=[DataRequired(message='客户名称不能为空')])
    identification_code = StringField('识别编码', render_kw={'readonly': True})
    pallet_count = IntegerField('板数', validators=[NumberRange(min=0, message='板数必须为正数'), validate_pallet_package_count])
    package_count = IntegerField('件数', validators=[NumberRange(min=0, message='件数必须为正数'), validate_pallet_package_count])
    weight = FloatField('重量(kg)', validators=[Optional(), NumberRange(min=0, message='重量必须为正数')])
    volume = FloatField('体积(m³)', validators=[Optional(), NumberRange(min=0, message='体积必须为正数')])
    order_type = SelectField('订单类型', choices=[
        ('', '请选择订单类型'),
        ('原车出境', '原车出境'),
        ('换车出境', '换车出境'),
        ('零担', '零担'),
        ('TP订单', 'TP订单')
    ], validators=[Optional()])
    export_mode = SelectField('出境模式', choices=[
        ('', '请选择出境模式'),
        ('保税', '保税'),
        ('清关', '清关')
    ], validators=[Optional()])
    customs_broker = StringField('报关行', validators=[Optional()])
    location = StringField('库位', validators=[Optional()])
    documents = StringField('单据', validators=[Optional()])
    service_staff = StringField('跟单客服', validators=[DataRequired(message='跟单客服不能为空')])
    submit = SubmitField('提交') 

# 保持向下兼容
InboundRecordEditForm = InboundRecordEditForm2

class OutboundRecordForm(FlaskForm):
    """出库记录表单"""
    outbound_time = DateTimeField('出库时间', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired(message='出库时间不能为空')])
    plate_number = StringField('出库车牌', validators=[DataRequired(message='出库车牌不能为空')])
    customer_name = StringField('客户名称', validators=[DataRequired(message='客户名称不能为空')])
    pallet_count = IntegerField('板数', validators=[DataRequired(message='板数不能为空'), NumberRange(min=0, message='板数必须为正数')])
    package_count = IntegerField('件数', validators=[DataRequired(message='件数不能为空'), NumberRange(min=0, message='件数必须为正数')])
    weight = FloatField('重量(kg)', validators=[DataRequired(message='重量不能为空'), NumberRange(min=0, message='重量必须为正数')])
    volume = FloatField('体积(m³)', validators=[DataRequired(message='体积不能为空'), NumberRange(min=0, message='体积必须为正数')])
    destination = StringField('目的地', validators=[Optional()])
    transport_company = StringField('运输公司', validators=[Optional()])
    service_staff = StringField('跟单客服', validators=[Optional()])
    remarks = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('提交')