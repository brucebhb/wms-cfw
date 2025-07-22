/**
 * 集成用户权限管理器
 */
class UserPermissionManager {
    constructor() {
        this.currentUserId = null;
        this.permissionDefinitions = null;
        this.userPermissions = null;
        this.isSaving = false; // 防止重复保存
        console.log('UserPermissionManager 构造函数被调用');
        this.init();
    }

    init() {
        console.log('UserPermissionManager 初始化开始');
        this.bindEvents();
        this.loadPermissionDefinitions();
        console.log('UserPermissionManager 初始化完成');
    }

    bindEvents() {
        console.log('绑定权限管理器事件');
        // 权限配置按钮事件
        document.addEventListener('click', (e) => {
            // 查找最近的配置权限按钮（处理点击图标的情况）
            const button = e.target.closest('.config-permissions-btn');
            if (button) {
                console.log('配置权限按钮被点击', button);
                const userId = button.dataset.userId;
                const userName = button.dataset.userName;
                console.log('用户信息:', { userId, userName });
                this.openPermissionConfig(userId, userName);
            }
        });

        // 菜单权限复选框联动事件
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('menu-permission')) {
                this.handleMenuPermissionChange(e.target);
            }
        });

        // 保存权限配置
        const saveBtn = document.getElementById('saveUserPermissions');
        if (saveBtn && !saveBtn.hasAttribute('data-listener-bound')) {
            saveBtn.addEventListener('click', () => {
                this.saveUserPermissions();
            });
            saveBtn.setAttribute('data-listener-bound', 'true');
        }

        // 全选/清空按钮（防止重复绑定）
        const buttonBindings = [
            { id: 'selectAllMenus', handler: () => this.selectAllMenus() },
            { id: 'clearAllMenus', handler: () => this.clearAllMenus() },
            { id: 'selectAllPages', handler: () => this.selectAllPages() },
            { id: 'clearAllPages', handler: () => this.clearAllPages() },
            { id: 'selectAllOperations', handler: () => this.selectAllOperations() },
            { id: 'clearAllOperations', handler: () => this.clearAllOperations() },
            { id: 'selectAllWarehouses', handler: () => this.selectAllWarehouses() },
            { id: 'clearAllWarehouses', handler: () => this.clearAllWarehouses() }
        ];

        buttonBindings.forEach(({ id, handler }) => {
            const btn = document.getElementById(id);
            if (btn && !btn.hasAttribute('data-listener-bound')) {
                btn.addEventListener('click', handler);
                btn.setAttribute('data-listener-bound', 'true');
            }
        });

        // 模态框关闭事件（处理用户手动关闭的情况）
        const modal = document.getElementById('userPermissionModal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', (e) => {
                // 只有在非程序化关闭时才处理（避免与closeModalAndRefresh重复）
                if (!e.target.dataset.programmaticClose) {
                    console.log('用户手动关闭权限配置模态框，重置状态');
                    this.forceCleanupModal();
                    this.resetState();
                }
            });
        }
    }

    async loadPermissionDefinitions() {
        try {
            const response = await fetch('/admin/api/permissions/definitions');
            const result = await response.json();

            if (result.success) {
                this.permissionDefinitions = result.data;
                console.log('权限定义加载成功:', this.permissionDefinitions);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('加载权限定义失败:', error);
            this.showAlert('加载权限定义失败: ' + error.message, 'danger');
        }
    }

    async openPermissionConfig(userId, userName) {
        console.log('openPermissionConfig 被调用', { userId, userName });
        this.currentUserId = userId;

        // 设置模态框标题
        const modalUserName = document.getElementById('modalUserName');
        if (modalUserName) {
            modalUserName.textContent = `${userName} - 权限配置`;
            console.log('模态框标题已设置');
        } else {
            console.error('找不到 modalUserName 元素');
        }

        try {
            console.log('开始加载用户权限');
            // 加载用户权限
            await this.loadUserPermissions(userId);

            console.log('开始渲染权限配置界面');
            // 渲染权限配置界面
            this.renderPermissionConfig();

            console.log('显示模态框');
            // 显示模态框
            const modalElement = document.getElementById('userPermissionModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log('模态框已显示');
            } else {
                console.error('找不到 userPermissionModal 元素');
            }

        } catch (error) {
            console.error('加载用户权限配置失败:', error);
            this.showAlert('加载用户权限配置失败: ' + error.message, 'danger');
        }
    }

    async loadUserBasicInfo(userId) {
        try {
            const response = await fetch(`/admin/api/users/${userId}`);
            const result = await response.json();
            
            if (result.success) {
                const user = result.data;
                
                // 填充用户基本信息表单
                document.getElementById('editUserId').value = user.id;
                document.getElementById('editUsername').value = user.username;
                document.getElementById('editRealName').value = user.real_name || '';
                document.getElementById('editEmail').value = user.email || '';
                document.getElementById('editWarehouse').value = user.warehouse_id || '';
                document.getElementById('editUserType').value = user.user_type || '';
                document.getElementById('editStatus').value = user.status || 'active';
                
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('加载用户基本信息失败:', error);
            throw error;
        }
    }

    async loadUserPermissions(userId) {
        try {
            const response = await fetch(`/admin/api/user-permissions/${userId}`);
            const result = await response.json();
            
            if (result.success) {
                this.userPermissions = result.data;
                console.log('用户权限加载成功:', this.userPermissions);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('加载用户权限失败:', error);
            throw error;
        }
    }

    renderPermissionConfig() {
        this.renderMenuPermissions();
        this.renderPagePermissions();
        this.renderOperationPermissions();
        this.renderWarehousePermissions();
    }

    renderMenuPermissions() {
        const container = document.getElementById('menuPermissions');
        
        if (!this.permissionDefinitions || !this.permissionDefinitions.menus) {
            container.innerHTML = '<p class="text-muted">暂无菜单权限数据</p>';
            return;
        }

        // 构建菜单树
        const menuTree = this.buildMenuTree(this.permissionDefinitions.menus);
        let html = '';

        menuTree.forEach(menu => {
            html += this.renderMenuNode(menu);
        });

        container.innerHTML = html;
    }

    buildMenuTree(menus) {
        const menuMap = {};
        const rootMenus = [];

        // 创建菜单映射
        menus.forEach(menu => {
            menu.children = [];
            menuMap[menu.menu_code] = menu;
        });

        // 构建树结构
        menus.forEach(menu => {
            if (menu.parent_menu_code && menuMap[menu.parent_menu_code]) {
                menuMap[menu.parent_menu_code].children.push(menu);
            } else {
                rootMenus.push(menu);
            }
        });

        return rootMenus;
    }

    renderMenuNode(menu) {
        const isGranted = this.isMenuGranted(menu.menu_code);
        const levelClass = `level-${menu.menu_level}`;

        let html = `
            <div class="menu-item ${levelClass}" data-menu-code="${menu.menu_code}" data-parent-code="${menu.parent_menu_code || ''}">
                <div class="form-check">
                    <input class="form-check-input menu-permission" type="checkbox"
                           id="menu_${menu.menu_code}" value="${menu.menu_code}"
                           data-menu-code="${menu.menu_code}"
                           data-parent-code="${menu.parent_menu_code || ''}"
                           ${isGranted ? 'checked' : ''}>
                    <label class="form-check-label" for="menu_${menu.menu_code}">
                        ${menu.menu_icon ? `<i class="${menu.menu_icon} me-1"></i>` : ''}
                        ${menu.menu_name}
                    </label>
                </div>
        `;

        if (menu.children && menu.children.length > 0) {
            menu.children.forEach(child => {
                html += this.renderMenuNode(child);
            });
        }

        html += '</div>';
        return html;
    }

    renderPagePermissions() {
        const container = document.getElementById('pagePermissions');
        
        if (!this.permissionDefinitions || !this.permissionDefinitions.pages) {
            container.innerHTML = '<p class="text-muted">暂无页面权限数据</p>';
            return;
        }

        // 按菜单分组页面权限
        const pagesByMenu = {};
        this.permissionDefinitions.pages.forEach(page => {
            if (!pagesByMenu[page.menu_code]) {
                pagesByMenu[page.menu_code] = [];
            }
            pagesByMenu[page.menu_code].push(page);
        });

        let html = '';
        Object.keys(pagesByMenu).forEach(menuCode => {
            const menuName = this.getMenuName(menuCode);
            html += `
                <div class="permission-group">
                    <div class="permission-group-title">${menuName}</div>
                    <div class="row">
            `;
            
            pagesByMenu[menuCode].forEach(page => {
                const isGranted = this.isPageGranted(page.page_code);
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="permission-item">
                            <div class="form-check">
                                <input class="form-check-input page-permission" type="checkbox"
                                       id="page_${page.page_code}" value="${page.page_code}"
                                       ${isGranted ? 'checked' : ''}>
                                <label class="form-check-label" for="page_${page.page_code}">
                                    ${page.page_name}
                                </label>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    renderOperationPermissions() {
        const container = document.getElementById('operationPermissions');
        
        if (!this.permissionDefinitions || !this.permissionDefinitions.operations) {
            container.innerHTML = '<p class="text-muted">暂无操作权限数据</p>';
            return;
        }

        // 按操作类型和仓库分组
        const operationsByType = {};
        const warehouseOperations = {};
        const systemOperations = [];

        this.permissionDefinitions.operations.forEach(operation => {
            const type = operation.operation_type || 'other';

            // 检查是否是仓库特定权限
            const warehouseMatch = operation.operation_code.match(/_(PH|KS|CD|PX)$/);
            if (warehouseMatch) {
                const warehouseCode = warehouseMatch[1];
                const warehouseName = this.getWarehouseName(warehouseCode);

                if (!warehouseOperations[warehouseName]) {
                    warehouseOperations[warehouseName] = {};
                }
                if (!warehouseOperations[warehouseName][type]) {
                    warehouseOperations[warehouseName][type] = [];
                }
                warehouseOperations[warehouseName][type].push(operation);
            } else {
                // 系统级权限
                systemOperations.push(operation);
            }
        });

        const typeNames = {
            'view': '查看权限',
            'create': '创建权限',
            'edit': '编辑权限',
            'delete': '删除权限',
            'export': '导出权限',
            'print': '打印权限',
            'approve': '审核权限',
            'manage': '管理权限',
            'other': '其他权限'
        };

        let html = '';

        // 渲染系统级权限
        if (systemOperations.length > 0) {
            html += `
                <div class="permission-group">
                    <div class="permission-group-title">
                        <i class="fas fa-cog me-2"></i>系统管理权限
                    </div>
                    <div class="row">
            `;

            systemOperations.forEach(operation => {
                const isGranted = this.isOperationGranted(operation.operation_code);
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="permission-item">
                            <div class="form-check">
                                <input class="form-check-input operation-permission" type="checkbox"
                                       id="operation_${operation.operation_code}" value="${operation.operation_code}"
                                       ${isGranted ? 'checked' : ''}>
                                <label class="form-check-label" for="operation_${operation.operation_code}">
                                    ${operation.operation_name}
                                </label>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        // 渲染仓库特定权限
        Object.keys(warehouseOperations).forEach(warehouseName => {
            html += `
                <div class="permission-group">
                    <div class="permission-group-title">
                        <i class="fas fa-warehouse me-2"></i>${warehouseName}权限
                    </div>
            `;

            const warehouseTypes = warehouseOperations[warehouseName];
            Object.keys(warehouseTypes).forEach(type => {
                html += `
                    <div class="permission-subgroup">
                        <div class="permission-subgroup-title">${typeNames[type] || type}</div>
                        <div class="row">
                `;

                warehouseTypes[type].forEach(operation => {
                    const isGranted = this.isOperationGranted(operation.operation_code);
                    html += `
                        <div class="col-md-6 mb-2">
                            <div class="permission-item">
                                <div class="form-check">
                                    <input class="form-check-input operation-permission" type="checkbox"
                                           id="operation_${operation.operation_code}" value="${operation.operation_code}"
                                           ${isGranted ? 'checked' : ''}>
                                    <label class="form-check-label" for="operation_${operation.operation_code}">
                                        ${operation.operation_name}
                                    </label>
                                </div>
                            </div>
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            });

            html += `
                </div>
            `;
        });

        container.innerHTML = html;
    }

    renderWarehousePermissions() {
        const container = document.getElementById('warehousePermissions');
        
        if (!this.permissionDefinitions || !this.permissionDefinitions.warehouses || !this.permissionDefinitions.warehouse_permissions) {
            container.innerHTML = '<p class="text-muted">暂无仓库权限数据</p>';
            return;
        }

        let html = '<div class="warehouse-permission-matrix">';
        
        this.permissionDefinitions.warehouses.forEach(warehouse => {
            html += `
                <div class="warehouse-item">
                    <h6>${warehouse.warehouse_name}</h6>
                    <div class="row">
            `;
            
            this.permissionDefinitions.warehouse_permissions.forEach(permission => {
                const isGranted = this.isWarehousePermissionGranted(warehouse.id, permission.warehouse_permission_code);
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="form-check">
                            <input class="form-check-input warehouse-permission" type="checkbox"
                                   id="warehouse_${warehouse.id}_${permission.warehouse_permission_code}"
                                   value="${warehouse.id}:${permission.warehouse_permission_code}"
                                   ${isGranted ? 'checked' : ''}>
                            <label class="form-check-label" for="warehouse_${warehouse.id}_${permission.warehouse_permission_code}">
                                ${permission.warehouse_permission_name}
                            </label>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    // 权限检查方法
    isMenuGranted(menuCode) {
        return this.userPermissions?.menu_permissions?.some(p => p.menu_code === menuCode && p.is_granted) || false;
    }

    isPageGranted(pageCode) {
        return this.userPermissions?.page_permissions?.some(p => p.page_code === pageCode && p.is_granted) || false;
    }

    isOperationGranted(operationCode) {
        return this.userPermissions?.operation_permissions?.some(p => p.operation_code === operationCode && p.is_granted) || false;
    }

    isWarehousePermissionGranted(warehouseId, permissionCode) {
        return this.userPermissions?.warehouse_permissions?.some(p =>
            p.warehouse_id === warehouseId && p.warehouse_permission_code === permissionCode && p.is_granted
        ) || false;
    }

    getWarehouseName(warehouseCode) {
        const warehouseNames = {
            'PH': '平湖仓',
            'KS': '昆山仓',
            'CD': '成都仓',
            'PX': '凭祥北投仓'
        };
        return warehouseNames[warehouseCode] || warehouseCode;
    }

    // 处理菜单权限联动
    handleMenuPermissionChange(checkbox) {
        const menuCode = checkbox.dataset.menuCode;
        const isChecked = checkbox.checked;

        if (isChecked) {
            // 如果勾选了菜单，自动勾选所有子菜单
            this.checkChildMenus(menuCode, true);
            // 如果所有兄弟菜单都被勾选，自动勾选父菜单
            this.checkParentMenuIfAllSiblingsChecked(menuCode);
        } else {
            // 如果取消勾选菜单，自动取消勾选所有子菜单和父菜单
            this.checkChildMenus(menuCode, false);
            this.uncheckParentMenus(menuCode);
        }
    }

    // 勾选/取消勾选所有子菜单
    checkChildMenus(parentMenuCode, checked) {
        const childMenus = this.getChildMenus(parentMenuCode);
        childMenus.forEach(childCode => {
            const childCheckbox = document.getElementById(`menu_${childCode}`);
            if (childCheckbox) {
                childCheckbox.checked = checked;
                // 递归处理子菜单的子菜单
                this.checkChildMenus(childCode, checked);
            }
        });
    }

    // 取消勾选所有父菜单
    uncheckParentMenus(menuCode) {
        const parentCode = this.getParentMenuCode(menuCode);
        if (parentCode) {
            const parentCheckbox = document.getElementById(`menu_${parentCode}`);
            if (parentCheckbox) {
                parentCheckbox.checked = false;
                // 递归处理父菜单的父菜单
                this.uncheckParentMenus(parentCode);
            }
        }
    }

    // 检查是否所有兄弟菜单都被勾选，如果是则勾选父菜单
    checkParentMenuIfAllSiblingsChecked(menuCode) {
        const parentCode = this.getParentMenuCode(menuCode);
        if (parentCode) {
            const siblingCodes = this.getChildMenus(parentCode);
            const allSiblingsChecked = siblingCodes.every(siblingCode => {
                const siblingCheckbox = document.getElementById(`menu_${siblingCode}`);
                return siblingCheckbox && siblingCheckbox.checked;
            });

            if (allSiblingsChecked) {
                const parentCheckbox = document.getElementById(`menu_${parentCode}`);
                if (parentCheckbox) {
                    parentCheckbox.checked = true;
                    // 递归检查父菜单的父菜单
                    this.checkParentMenuIfAllSiblingsChecked(parentCode);
                }
            }
        }
    }

    // 获取子菜单代码列表
    getChildMenus(parentMenuCode) {
        if (!this.permissionDefinitions?.menus) return [];
        return this.permissionDefinitions.menus
            .filter(menu => menu.parent_menu_code === parentMenuCode)
            .map(menu => menu.menu_code);
    }

    // 获取父菜单代码
    getParentMenuCode(menuCode) {
        if (!this.permissionDefinitions?.menus) return null;
        const menu = this.permissionDefinitions.menus.find(m => m.menu_code === menuCode);
        return menu ? menu.parent_menu_code : null;
    }

    // 辅助方法
    getMenuName(menuCode) {
        const menu = this.permissionDefinitions?.menus?.find(m => m.menu_code === menuCode);
        return menu ? menu.menu_name : menuCode;
    }

    // 保存用户权限配置
    async saveUserPermissions() {
        if (!this.currentUserId) {
            this.showAlert('请先选择用户', 'warning');
            return;
        }

        // 防止重复保存
        if (this.isSaving) {
            console.log('正在保存中，忽略重复请求');
            return;
        }

        this.isSaving = true;
        console.log('开始保存权限配置');

        try {
            // 收集所有权限数据
            const permissions = this.collectPermissions();

            console.log('保存权限配置:', permissions);

            // 保存权限配置
            const response = await fetch(`/admin/api/user-permissions/${this.currentUserId}/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(permissions)
            });

            const result = await response.json();

            if (result.success) {
                console.log('权限配置保存成功，显示提示');

                // 显示成功提示
                this.showAlert('权限配置保存成功！', 'success');

                // 延迟关闭模态框，确保用户看到成功消息
                setTimeout(() => {
                    this.closeModalAndRefresh();
                }, 1500);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('保存权限配置失败:', error);

            // 显示失败提示
            this.showAlert('保存权限配置失败: ' + error.message, 'danger');
        } finally {
            // 重置保存状态
            this.isSaving = false;
            console.log('保存状态已重置');
        }
    }

    // 关闭模态框并刷新页面
    closeModalAndRefresh() {
        console.log('开始关闭模态框并刷新');

        try {
            // 获取模态框元素
            const modalElement = document.getElementById('userPermissionModal');
            if (!modalElement) {
                console.error('找不到模态框元素');
                return;
            }

            // 获取模态框实例
            let modal = bootstrap.Modal.getInstance(modalElement);

            // 如果没有实例，创建一个新的
            if (!modal) {
                console.log('创建新的模态框实例');
                modal = new bootstrap.Modal(modalElement);
            }

            // 标记为程序化关闭
            modalElement.dataset.programmaticClose = 'true';

            // 监听模态框完全关闭事件
            modalElement.addEventListener('hidden.bs.modal', () => {
                console.log('模态框已完全关闭');

                // 清除程序化关闭标记
                delete modalElement.dataset.programmaticClose;

                // 强制清理所有模态框相关的类和属性
                this.forceCleanupModal();

                // 重置权限管理器状态
                this.resetState();

                // 刷新用户列表
                this.refreshUserList();

            }, { once: true }); // 只执行一次

            // 关闭模态框
            console.log('关闭模态框');
            modal.hide();

        } catch (error) {
            console.error('关闭模态框时出错:', error);
            // 如果出错，强制清理并刷新页面
            this.forceCleanupModal();
            window.location.reload();
        }
    }

    // 强制清理模态框状态
    forceCleanupModal() {
        console.log('强制清理模态框状态');

        // 移除所有模态框相关的类
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';

        // 移除所有背景遮罩
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
        });

        // 重置模态框元素状态
        const modalElement = document.getElementById('userPermissionModal');
        if (modalElement) {
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            modalElement.setAttribute('aria-hidden', 'true');
            modalElement.removeAttribute('aria-modal');
        }
    }

    // 刷新用户列表
    refreshUserList() {
        console.log('刷新用户列表');

        if (typeof window.loadUsers === 'function') {
            console.log('调用 loadUsers 函数');
            window.loadUsers(window.currentPage || 1);
        } else {
            console.log('loadUsers 函数不存在，刷新页面');
            window.location.reload();
        }
    }

    // 重置权限管理器状态
    resetState() {
        console.log('重置权限管理器状态');
        this.currentUserId = null;
        this.userPermissions = null;
        this.isSaving = false; // 重置保存状态

        // 清空表单
        const userBasicForm = document.getElementById('userBasicForm');
        if (userBasicForm) {
            userBasicForm.reset();
        }

        // 清空权限配置区域
        const permissionConfigArea = document.getElementById('permissionConfigArea');
        if (permissionConfigArea) {
            permissionConfigArea.innerHTML = '';
        }
    }

    async saveUserBasicInfo() {
        const formData = new FormData(document.getElementById('userBasicForm'));
        const userData = Object.fromEntries(formData.entries());

        const response = await fetch(`/admin/api/users/${this.currentUserId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message);
        }
    }

    collectPermissions() {
        const permissions = {
            menu_permissions: [],
            page_permissions: [],
            operation_permissions: [],
            warehouse_permissions: []
        };

        // 收集菜单权限
        document.querySelectorAll('.menu-permission:checked').forEach(checkbox => {
            permissions.menu_permissions.push({
                menu_code: checkbox.value,
                is_granted: true
            });
        });

        // 收集页面权限
        document.querySelectorAll('.page-permission:checked').forEach(checkbox => {
            permissions.page_permissions.push({
                page_code: checkbox.value,
                is_granted: true
            });
        });

        // 收集操作权限
        document.querySelectorAll('.operation-permission:checked').forEach(checkbox => {
            permissions.operation_permissions.push({
                operation_code: checkbox.value,
                is_granted: true
            });
        });

        // 收集仓库权限
        document.querySelectorAll('.warehouse-permission:checked').forEach(checkbox => {
            const [warehouseId, permissionCode] = checkbox.value.split(':');
            permissions.warehouse_permissions.push({
                warehouse_id: parseInt(warehouseId),
                warehouse_permission_code: permissionCode,
                is_granted: true
            });
        });

        return permissions;
    }

    // 全选/清空功能
    selectAllMenus() {
        document.querySelectorAll('.menu-permission').forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    clearAllMenus() {
        document.querySelectorAll('.menu-permission').forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    selectAllPages() {
        document.querySelectorAll('.page-permission').forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    clearAllPages() {
        document.querySelectorAll('.page-permission').forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    selectAllOperations() {
        document.querySelectorAll('.operation-permission').forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    clearAllOperations() {
        document.querySelectorAll('.operation-permission').forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    selectAllWarehouses() {
        document.querySelectorAll('.warehouse-permission').forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    clearAllWarehouses() {
        document.querySelectorAll('.warehouse-permission').forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    showAlert(message, type = 'info') {
        console.log(`showAlert 被调用: ${message} (${type})`);

        // 优先使用消息系统，如果不可用则使用自定义提示框
        try {
            // 方式1: 尝试使用消息系统
            if (typeof showMessage === 'function') {
                console.log('使用消息系统显示提示');
                showMessage(message, type.toUpperCase());
                console.log('消息系统调用成功，结束showAlert');
                return;
            }
        } catch (e) {
            console.log('消息系统调用失败:', e);
        }

        // 方式2: 如果消息系统不可用，使用自定义提示框
        try {
            console.log('消息系统不可用，创建自定义提示框');
            this.createCustomAlert(message, type);
        } catch (e) {
            console.log('自定义提示框创建失败，使用基本alert:', e);
            alert(`${this.getAlertIcon(type)} ${message}`);
        }
    }

    createCustomAlert(message, type) {
        try {
            console.log('开始创建自定义提示框');

            // 移除现有的提示框
            const existingAlert = document.querySelector('.custom-alert');
            if (existingAlert) {
                existingAlert.remove();
                console.log('移除了现有提示框');
            }

            // 创建提示框
            const alertDiv = document.createElement('div');
            const alertClass = this.getBootstrapAlertClass(type);
            const alertIcon = this.getAlertIcon(type);

            alertDiv.className = `alert alert-${alertClass} alert-dismissible fade show custom-alert`;
            alertDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            `;

            alertDiv.innerHTML = `
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 8px;">${alertIcon}</span>
                    <span style="flex: 1;">${message}</span>
                    <button type="button" class="btn-close ms-2" onclick="this.parentElement.parentElement.remove()"></button>
                </div>
            `;

            // 添加到页面
            document.body.appendChild(alertDiv);
            console.log('提示框已添加到页面');

            // 自动移除
            setTimeout(() => {
                if (alertDiv && alertDiv.parentNode) {
                    alertDiv.remove();
                    console.log('提示框已自动移除');
                }
            }, 5000);

        } catch (error) {
            console.error('创建自定义提示框失败:', error);
            // 最后的降级方案
            alert(`${this.getAlertIcon(type)} ${message}`);
        }
    }

    getBootstrapAlertClass(type) {
        const typeMap = {
            'success': 'success',
            'danger': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }

    getAlertIcon(type) {
        const iconMap = {
            'success': '✅',
            'danger': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return iconMap[type] || 'ℹ️';
    }
}
