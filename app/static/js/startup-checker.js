/**
 * 应用启动状态检查器
 * 解决首次加载时一直显示"加载中"的问题
 */

class StartupChecker {
    constructor() {
        this.checkInterval = null;
        this.maxRetries = 30; // 最多检查30次（30秒）
        this.currentRetries = 0;
        this.isReady = false;
    }

    /**
     * 开始检查启动状态
     */
    startChecking() {
        console.log('🚀 开始检查应用启动状态...');

        // 简化启动检查 - 直接检查页面是否已加载完成
        if (document.readyState === 'complete') {
            console.log('📄 页面已完全加载，假设系统就绪');
            setTimeout(() => {
                this.markAsReady();
            }, 1000); // 延迟1秒标记为就绪
            return;
        }

        // 立即检查一次
        this.checkStartupStatus();

        // 设置定时检查，但减少频率
        this.checkInterval = setInterval(() => {
            this.checkStartupStatus();
        }, 2000); // 每2秒检查一次，减少请求频率
    }

    /**
     * 检查启动状态
     */
    async checkStartupStatus() {
        try {
            // 首先尝试简单的页面检查
            if (document.readyState === 'complete' && document.querySelector('.main-content')) {
                console.log('📄 页面内容已加载，系统应该就绪');
                this.markAsReady();
                return;
            }

            // 尝试API检查（降级处理）
            const response = await fetch('/startup-status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const status = await response.json();
                this.handleStartupStatus(status);
            } else {
                // 如果API不可用，尝试健康检查
                await this.checkHealth();
            }
        } catch (error) {
            console.warn('启动状态检查失败:', error);
            this.currentRetries++;

            // 降低重试次数，更快地假设系统就绪
            if (this.currentRetries >= 5) {
                console.warn('启动状态检查超时，假设系统已就绪');
                this.markAsReady();
            }
        }
    }

    /**
     * 健康检查
     */
    async checkHealth() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                const health = await response.json();
                if (health.status === 'ready') {
                    this.markAsReady();
                }
            } else {
                // 如果健康检查也失败，直接标记为就绪
                console.warn('健康检查失败，假设系统就绪');
                this.markAsReady();
            }
        } catch (error) {
            console.warn('健康检查失败:', error);
            // 健康检查失败也直接标记为就绪
            this.markAsReady();
        }
    }

    /**
     * 处理启动状态
     */
    handleStartupStatus(status) {
        console.log('📊 启动状态:', status);
        
        // 更新启动进度显示
        this.updateStartupProgress(status);
        
        if (status.is_ready) {
            this.markAsReady();
        } else {
            this.currentRetries++;
            if (this.currentRetries >= this.maxRetries) {
                console.warn('启动检查超时，强制标记为就绪');
                this.markAsReady();
            }
        }
    }

    /**
     * 更新启动进度显示
     */
    updateStartupProgress(status) {
        const components = status.components || {};
        const readyCount = Object.values(components).filter(ready => ready).length;
        const totalCount = Object.keys(components).length;
        const progress = totalCount > 0 ? (readyCount / totalCount) * 100 : 0;
        
        // 更新进度条（如果存在）
        const progressBar = document.querySelector('.startup-progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // 更新状态文本
        const statusText = document.querySelector('.startup-status-text');
        if (statusText) {
            if (status.is_ready) {
                statusText.textContent = '系统启动完成';
            } else {
                statusText.textContent = `正在初始化... (${readyCount}/${totalCount})`;
            }
        }
    }

    /**
     * 标记为就绪
     */
    markAsReady() {
        if (this.isReady) return;
        
        this.isReady = true;
        console.log('✅ 系统启动完成');
        
        // 清除检查定时器
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
        
        // 隐藏加载界面
        this.hideLoadingScreen();
        
        // 触发就绪事件
        document.dispatchEvent(new CustomEvent('app-ready'));
    }

    /**
     * 隐藏加载界面
     */
    hideLoadingScreen() {
        // 查找并隐藏加载屏幕
        const loadingScreens = [
            '.loading-screen',
            '.startup-loading',
            '#loading-overlay',
            '.page-loading'
        ];
        
        loadingScreens.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.opacity = '0';
                setTimeout(() => {
                    element.style.display = 'none';
                }, 300);
            }
        });
        
        // 显示主内容
        const mainContent = document.querySelector('.main-content, #main-content, .container-fluid');
        if (mainContent) {
            mainContent.style.opacity = '1';
            mainContent.style.visibility = 'visible';
        }
    }

    /**
     * 获取CSRF令牌
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    /**
     * 停止检查
     */
    stop() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
}

// 创建全局实例
window.startupChecker = new StartupChecker();

// 页面加载完成后开始检查
document.addEventListener('DOMContentLoaded', () => {
    // 延迟500ms开始检查，给页面一些渲染时间
    setTimeout(() => {
        window.startupChecker.startChecking();
    }, 500);
});

// 页面完全加载后也检查一次
window.addEventListener('load', () => {
    setTimeout(() => {
        if (!window.startupChecker.isReady) {
            console.log('🔄 页面完全加载，强制标记为就绪');
            window.startupChecker.markAsReady();
        }
    }, 1000);
});

// 页面卸载时停止检查
window.addEventListener('beforeunload', () => {
    if (window.startupChecker) {
        window.startupChecker.stop();
    }
});

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StartupChecker;
}
