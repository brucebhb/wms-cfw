from flask import render_template, redirect, url_for, flash, request, session, jsonify, make_response
from flask_login import login_user, logout_user, current_user, login_required
from app import db, csrf
from app.auth import bp
from app.models import User, UserLoginLog, AuditLog
from datetime import datetime
import json


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.status != 'active':
                flash('账号已被禁用，请联系管理员', 'error')
                return render_template('auth/login.html')
            
            # 登录成功
            login_user(user, remember=remember_me)

            # 设置永久会话，6小时后自动过期
            session.permanent = True

            # 更新最后登录时间
            user.last_login_at = datetime.now()
            db.session.commit()

            # 记录登录日志
            login_log = UserLoginLog(
                user_id=user.id,
                login_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                status='success'
            )
            db.session.add(login_log)

            # 记录审计日志
            audit_log = AuditLog(
                user_id=user.id,
                warehouse_id=user.warehouse_id,
                module='auth',
                action='login',
                resource_type='user',
                resource_id=str(user.id),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()

            # 存储用户信息到session，包括登录时间
            session['user_id'] = user.id
            session['warehouse_id'] = user.warehouse_id
            session['warehouse_name'] = user.warehouse.warehouse_name if user.warehouse else None
            session['login_time'] = datetime.now().isoformat()
            
            flash(f'欢迎回来，{user.real_name}！', 'success')
            
            # 重定向到原来要访问的页面
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            # 登录失败
            if user:
                login_log = UserLoginLog(
                    user_id=user.id,
                    login_ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    status='failed'
                )
                db.session.add(login_log)
                db.session.commit()
            
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')


@bp.route('/test')
def test():
    """测试路由"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试页面</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>测试页面</h1>
        <button onclick="testLogout()">点击测试登出</button>

        <script>
        function testLogout() {
            alert("JavaScript正在执行...");
            console.log("测试登出开始");

            // 清除所有cookie
            document.cookie.split(";").forEach(function(c) {
                document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
            });

            // 清除localStorage和sessionStorage
            localStorage.clear();
            sessionStorage.clear();

            alert("即将跳转到登录页面");
            window.location.href = '/auth/login';
        }
        </script>
    </body>
    </html>
    '''

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """用户登出"""
    from flask_login import logout_user

    print("=== 服务器端登出开始 ===")

    # 执行登出
    if current_user.is_authenticated:
        print(f"登出用户: {current_user.username}")
        logout_user()

    # 清除session
    session.clear()
    print("Session已清除")

    # 设置响应头防止缓存
    response = make_response(redirect(url_for('auth.login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    # 清除所有可能的session cookie
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)

    print("=== 服务器端登出完成，重定向到登录页面 ===")
    flash('您已成功登出', 'info')

    return response


@bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('auth/profile.html', user=current_user)


@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([old_password, new_password, confirm_password]):
            flash('请填写所有字段', 'error')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(old_password):
            flash('原密码错误', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('新密码和确认密码不一致', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('auth/change_password.html')
        
        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='auth',
            action='change_password',
            resource_type='user',
            resource_id=str(current_user.id),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('密码修改成功', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')


@bp.route('/refresh_session', methods=['POST'])
@login_required
def refresh_session():
    """刷新会话时间"""
    try:
        # 更新会话中的登录时间
        session['login_time'] = datetime.now().isoformat()

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='auth',
            action='refresh_session',
            resource_type='session',
            resource_id=str(current_user.id),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()

        return {'success': True, 'message': '会话已刷新'}
    except Exception as e:
        return {'success': False, 'message': f'刷新失败: {str(e)}'}, 500


@bp.route('/change-password', methods=['POST'])
@csrf.exempt
@login_required
def change_password_api():
    """修改密码API"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({'success': False, 'message': '请填写所有字段'})

        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': '当前密码错误'})

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度至少6位'})

        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='auth',
            action='change_password',
            resource_type='user',
            resource_id=str(current_user.id),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({'success': True, 'message': '密码修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'})


@bp.route('/update-profile', methods=['POST'])
@csrf.exempt
@login_required
def update_profile_api():
    """更新个人资料API"""
    try:
        data = request.get_json()
        real_name = data.get('real_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        # 更新用户信息
        if real_name:
            current_user.real_name = real_name
        if email:
            current_user.email = email
        if phone:
            current_user.phone = phone

        db.session.commit()

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='auth',
            action='update_profile',
            resource_type='user',
            resource_id=str(current_user.id),
            old_values={'real_name': current_user.real_name, 'email': current_user.email, 'phone': current_user.phone},
            new_values={'real_name': real_name, 'email': email, 'phone': phone},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()

        return jsonify({'success': True, 'message': '资料更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})





def check_permission(permission_code, warehouse_id=None):
    """检查当前用户权限的装饰器函数"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission_code, warehouse_id):
                flash('您没有权限访问此功能', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


@bp.route('/check_status')
def check_status():
    """检查用户登录状态"""
    if current_user.is_authenticated:
        return jsonify({
            'status': 'authenticated',
            'user': current_user.username,
            'warehouse': current_user.warehouse.warehouse_name if current_user.warehouse else None
        })
    else:
        return jsonify({'status': 'unauthenticated'}), 401
