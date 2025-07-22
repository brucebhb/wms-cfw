/**
 * 操作增强器
 * 为各种操作添加统一的提示和反馈
 */

class OperationEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceFormSubmissions();
        this.enhanceAjaxRequests();
        this.enhanceButtonClicks();
        this.enhanceFileUploads();
        this.enhanceDeleteOperations();
    }

    /**
     * 增强表单提交
     */
    enhanceFormSubmissions() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (!form.classList.contains('no-enhance')) {
                this.handleFormSubmit(form, e);
            }
        });
    }

    /**
     * 处理表单提交
     */
    handleFormSubmit(form, event) {
        // 显示加载状态
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.textContent || submitBtn.value;
            submitBtn.disabled = true;
            submitBtn.textContent = '提交中...';
            
            // 恢复按钮状态的函数
            const restoreButton = () => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            };

            // 设置超时恢复
            setTimeout(restoreButton, 10000);
            
            // 监听页面变化来恢复按钮
            const observer = new MutationObserver(() => {
                if (!document.contains(submitBtn)) {
                    observer.disconnect();
                } else if (!submitBtn.disabled) {
                    observer.disconnect();
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
        }

        // 显示提交提示
        showInfo('正在提交数据，请稍候...');
    }

    /**
     * 增强AJAX请求
     */
    enhanceAjaxRequests() {
        // 暂时禁用fetch拦截，避免与页面加载优化器冲突
        // 只在特定情况下启用
        if (window.location.pathname.includes('/api/')) {
            this.setupApiRequestHandling();
        }
    }

    /**
     * 设置API请求处理
     */
    setupApiRequestHandling() {
        // 使用事件监听而不是拦截fetch
        document.addEventListener('ajaxStart', () => {
            showInfo('正在处理请求...');
        });

        document.addEventListener('ajaxComplete', () => {
            // 请求完成处理
        });
    }

    /**
     * 增强的fetch请求 - 暂时禁用以避免冲突
     */
    async enhancedFetch(originalFetch, url, options) {
        // 暂时直接返回原始fetch结果，避免与页面加载优化器冲突
        return originalFetch(url, options);

        /* 原始代码暂时注释
        try {
            const response = await originalFetch(url, options);

            // 处理响应
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    this.handleApiResponse(url, data, options.method || 'GET');
                    return new Response(JSON.stringify(data), {
                        status: response.status,
                        statusText: response.statusText,
                        headers: response.headers
                    });
                }
            } else {
                this.handleApiError(url, response);
            }

            return response;
        } catch (error) {
            this.handleNetworkError(url, error);
            throw error;
        }
        */
    }

    /**
     * 处理API响应
     */
    handleApiResponse(url, data, method) {
        // 根据URL和响应数据显示相应提示
        // 注意：前端仓入库页面有自己的消息处理逻辑，这里跳过
        if (url.includes('/api/frontend/add-inbound') || url.includes('/api/frontend/batch-receive')) {
            return; // 跳过前端仓入库的自动消息处理
        }

        if (data.success) {
            if (url.includes('/outbound/') && method === 'POST') {
                if (data.operation_type === 'chunjiang_outbound') {
                    showSuccess('🚛 春疆货场出库完成');
                    if (data.inventory_updated) {
                        showInfo('📦 库存已自动更新');
                    }
                } else {
                    showSuccess('📋 出库记录保存成功');
                }
            } else if (url.includes('/inbound/') && method === 'POST') {
                showSuccess('📥 入库记录保存成功');
            } else if (url.includes('/inventory/') && method === 'PUT') {
                showSuccess('📦 库存更新成功');
            }
        } else if (data.message) {
            showError(data.message);
        }
    }

    /**
     * 处理API错误
     */
    handleApiError(url, response) {
        if (response.status === 403) {
            showError('❌ 权限不足，无法执行此操作');
        } else if (response.status === 404) {
            showError('❌ 请求的资源不存在');
        } else if (response.status >= 500) {
            showError('❌ 服务器错误，请稍后重试');
        } else {
            showError(`❌ 请求失败 (${response.status})`);
        }
    }

    /**
     * 处理网络错误
     */
    handleNetworkError(url, error) {
        console.error('网络请求失败:', url, error);
        showError('❌ 网络连接失败，请检查网络后重试');
    }

    /**
     * 增强按钮点击
     */
    enhanceButtonClicks() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn');
            if (button && !button.classList.contains('no-enhance')) {
                this.handleButtonClick(button, e);
            }
        });
    }

    /**
     * 处理按钮点击
     */
    handleButtonClick(button, event) {
        const action = button.dataset.action;
        const confirm = button.dataset.confirm;
        
        // 处理确认对话框
        if (confirm) {
            event.preventDefault();
            this.showConfirmDialog(confirm, () => {
                this.executeButtonAction(button, action);
            });
            return;
        }

        // 处理特定操作
        if (action) {
            this.executeButtonAction(button, action);
        }
    }

    /**
     * 显示确认对话框
     */
    async showConfirmDialog(message, callback) {
        const confirmed = await showConfirm(message, {
            title: '操作确认',
            type: 'warning'
        });
        
        if (confirmed) {
            callback();
        }
    }

    /**
     * 执行按钮操作
     */
    executeButtonAction(button, action) {
        switch (action) {
            case 'delete':
                showWarning('正在删除，请稍候...');
                break;
            case 'save':
                showInfo('正在保存，请稍候...');
                break;
            case 'export':
                showInfo('正在导出数据，请稍候...');
                break;
            case 'import':
                showInfo('正在导入数据，请稍候...');
                break;
            case 'refresh':
                showInfo('正在刷新数据...');
                break;
            default:
                // 默认操作提示
                if (button.textContent.includes('保存')) {
                    showInfo('正在保存，请稍候...');
                } else if (button.textContent.includes('删除')) {
                    showWarning('正在删除，请稍候...');
                } else if (button.textContent.includes('导出')) {
                    showInfo('正在导出，请稍候...');
                }
                break;
        }
    }

    /**
     * 增强文件上传
     */
    enhanceFileUploads() {
        document.addEventListener('change', (e) => {
            const input = e.target;
            if (input.type === 'file' && !input.classList.contains('no-enhance')) {
                this.handleFileUpload(input);
            }
        });
    }

    /**
     * 处理文件上传
     */
    handleFileUpload(input) {
        const files = input.files;
        if (files.length > 0) {
            const file = files[0];
            
            // 文件大小检查
            if (file.size > 10 * 1024 * 1024) { // 10MB
                showWarning('⚠️ 文件过大，建议选择小于10MB的文件');
            }
            
            // 文件类型检查
            const allowedTypes = input.accept ? input.accept.split(',').map(t => t.trim()) : [];
            if (allowedTypes.length > 0) {
                const fileType = file.type;
                const fileName = file.name.toLowerCase();
                
                const isAllowed = allowedTypes.some(type => {
                    if (type.startsWith('.')) {
                        return fileName.endsWith(type);
                    }
                    return fileType.includes(type.replace('*', ''));
                });
                
                if (!isAllowed) {
                    showError('❌ 文件格式不支持，请选择正确的文件类型');
                    input.value = '';
                    return;
                }
            }
            
            showSuccess(`📁 已选择文件：${file.name}`);
        }
    }

    /**
     * 增强删除操作
     */
    enhanceDeleteOperations() {
        document.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('[data-action="delete"], .delete-btn, .btn-delete');
            if (deleteBtn && !deleteBtn.classList.contains('no-enhance')) {
                e.preventDefault();
                this.handleDeleteOperation(deleteBtn);
            }
        });
    }

    /**
     * 处理删除操作
     */
    async handleDeleteOperation(button) {
        const itemName = button.dataset.itemName || '此项';
        const confirmMessage = button.dataset.confirm || `确定要删除${itemName}吗？此操作不可撤销。`;
        
        const confirmed = await showConfirm(confirmMessage, {
            title: '删除确认',
            confirmText: '确定删除',
            cancelText: '取消',
            type: 'danger'
        });
        
        if (confirmed) {
            // 执行删除操作
            const href = button.href || button.dataset.href;
            if (href) {
                showInfo('正在删除，请稍候...');
                window.location.href = href;
            } else {
                // 触发原始点击事件
                button.classList.add('no-enhance');
                button.click();
                button.classList.remove('no-enhance');
            }
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.operationEnhancer = new OperationEnhancer();
    
    // 显示系统就绪消息
    setTimeout(() => {
        showInfo('💡 操作提示系统已就绪', { duration: 2000 });
    }, 1000);
});

// 导出到全局作用域
window.OperationEnhancer = OperationEnhancer;
