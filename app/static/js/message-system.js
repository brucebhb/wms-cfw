/**
 * 统一消息提示系统
 * 提供成功、错误、警告、信息等多种类型的消息提示
 */

// 消息类型枚举
const MessageType = {
    SUCCESS: 'success',
    ERROR: 'danger', 
    WARNING: 'warning',
    INFO: 'info'
};

// 消息配置
const MessageConfig = {
    [MessageType.SUCCESS]: {
        icon: '✅',
        duration: 3000,
        sound: true
    },
    [MessageType.ERROR]: {
        icon: '❌',
        duration: 5000,
        sound: true
    },
    [MessageType.WARNING]: {
        icon: '⚠️',
        duration: 4000,
        sound: false
    },
    [MessageType.INFO]: {
        icon: 'ℹ️',
        duration: 3000,
        sound: false
    }
};

/**
 * 显示消息提示
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, danger, warning, info)
 * @param {object} options - 可选配置
 */
function showMessage(message, type = MessageType.INFO, options = {}) {
    // 确保成功消息使用正确的类型
    if (message && (message.includes('成功') || message.includes('添加')) && type !== MessageType.SUCCESS) {
        console.log('消息系统: 修正消息类型从', type, '到', MessageType.SUCCESS);
        type = MessageType.SUCCESS;
    }

    const config = { ...MessageConfig[type], ...options };
    
    // 创建消息元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed message-alert`;
    alertDiv.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: none;
        border-radius: 8px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <span class="me-2" style="font-size: 1.2em;">${config.icon}</span>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(alertDiv);
    
    // 播放提示音（如果启用）
    if (config.sound && options.sound !== false) {
        playNotificationSound(type);
    }
    
    // 自动移除
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 300);
        }
    }, config.duration);
    
    // 记录消息到控制台
    const logMethod = type === MessageType.ERROR ? 'error' :
                     type === MessageType.WARNING ? 'warn' : 'log';
    console[logMethod](`[${type.toUpperCase()}] ${message}`);

    // 调试信息：记录消息类型和配置
    console.debug(`Message type: ${type}, Config:`, config);
}

/**
 * 显示成功消息
 * @param {string} message - 消息内容
 * @param {object} options - 可选配置
 */
function showSuccess(message, options = {}) {
    showMessage(message, MessageType.SUCCESS, options);
}

/**
 * 显示错误消息
 * @param {string} message - 消息内容
 * @param {object} options - 可选配置
 */
function showError(message, options = {}) {
    showMessage(message, MessageType.ERROR, options);
}

/**
 * 显示警告消息
 * @param {string} message - 消息内容
 * @param {object} options - 可选配置
 */
function showWarning(message, options = {}) {
    showMessage(message, MessageType.WARNING, options);
}

/**
 * 显示信息消息
 * @param {string} message - 消息内容
 * @param {object} options - 可选配置
 */
function showInfo(message, options = {}) {
    showMessage(message, MessageType.INFO, options);
}

/**
 * 显示加载提示
 * @param {string} message - 加载消息
 * @returns {object} 加载提示对象，包含hide方法
 */
function showLoading(message = '正在处理，请稍候...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-overlay position-fixed';
    loadingDiv.style.cssText = `
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    loadingDiv.innerHTML = `
        <div class="bg-white p-4 rounded-3 text-center" style="min-width: 200px;">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="text-muted">${message}</div>
        </div>
    `;
    
    document.body.appendChild(loadingDiv);
    
    return {
        hide: function() {
            if (loadingDiv.parentNode) {
                loadingDiv.parentNode.removeChild(loadingDiv);
            }
        }
    };
}

/**
 * 显示确认对话框
 * @param {string} message - 确认消息
 * @param {object} options - 配置选项
 * @returns {Promise<boolean>} 用户选择结果
 */
function showConfirm(message, options = {}) {
    const config = {
        title: '确认操作',
        confirmText: '确认',
        cancelText: '取消',
        type: 'warning',
        ...options
    };
    
    return new Promise((resolve) => {
        const modalId = 'confirmModal_' + Date.now();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <span class="me-2">${MessageConfig[config.type]?.icon || '❓'}</span>
                                ${config.title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${config.cancelText}</button>
                            <button type="button" class="btn btn-${config.type === 'warning' ? 'warning' : 'primary'}" id="${modalId}_confirm">${config.confirmText}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        
        // 绑定事件
        document.getElementById(`${modalId}_confirm`).addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });
        
        document.getElementById(modalId).addEventListener('hidden.bs.modal', () => {
            document.getElementById(modalId).remove();
            resolve(false);
        });
        
        modal.show();
    });
}

/**
 * 播放提示音
 * @param {string} type - 消息类型
 */
function playNotificationSound(type) {
    try {
        // 创建音频上下文
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // 根据消息类型设置不同的音调
        const frequencies = {
            [MessageType.SUCCESS]: [523, 659, 784], // C-E-G 大三和弦
            [MessageType.ERROR]: [220, 220, 220],   // 低音A 重复
            [MessageType.WARNING]: [440, 554],      // A-C# 
            [MessageType.INFO]: [440]               // A
        };
        
        const freq = frequencies[type] || frequencies[MessageType.INFO];
        
        // 播放音序
        let time = audioContext.currentTime;
        freq.forEach((f, i) => {
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();
            
            osc.connect(gain);
            gain.connect(audioContext.destination);
            
            osc.frequency.setValueAtTime(f, time);
            gain.gain.setValueAtTime(0.1, time);
            gain.gain.exponentialRampToValueAtTime(0.01, time + 0.1);
            
            osc.start(time);
            osc.stop(time + 0.1);
            
            time += 0.1;
        });
    } catch (error) {
        // 静默处理音频错误
        console.debug('音频播放失败:', error);
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .message-alert {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
`;
document.head.appendChild(style);

// 导出到全局作用域
window.showMessage = showMessage;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.showLoading = showLoading;
window.showConfirm = showConfirm;

// 初始化消息系统
document.addEventListener('DOMContentLoaded', function() {
    console.log('消息系统已初始化');

    // 全局拦截器：确保成功消息使用正确的类型
    const originalShowMessage = window.showMessage;
    window.showMessage = function(message, type, options) {
        // 强制修正成功消息的类型
        if (message && (message.includes('成功') || message.includes('添加') || message.includes('保存')) && type === 'danger') {
            console.warn('全局拦截器: 修正错误的消息类型', type, '→', MessageType.SUCCESS);
            type = MessageType.SUCCESS;
        }

        return originalShowMessage.call(this, message, type, options);
    };

    console.log('全局消息拦截器已启用');
});
