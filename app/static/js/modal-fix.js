/**
 * Bootstrap 5 模态框修复脚本
 * 解决从Bootstrap 4迁移到Bootstrap 5时的兼容性问题
 */

(function() {
    'use strict';

    // 等待DOM和jQuery加载完成
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔧 模态框修复脚本开始执行...');

        // 修复所有现有的模态框
        fixExistingModals();

        // 监听动态添加的模态框
        observeModalChanges();

        console.log('✅ 模态框修复脚本执行完成');
    });

    /**
     * 修复现有的模态框
     */
    function fixExistingModals() {
        const modals = document.querySelectorAll('.modal');
        console.log(`🔍 发现 ${modals.length} 个模态框，开始修复...`);

        modals.forEach((modal, index) => {
            try {
                fixModalAttributes(modal);
                ensureModalInstance(modal);
                console.log(`✅ 模态框 ${modal.id || `modal-${index}`} 修复完成`);
            } catch (error) {
                console.error(`❌ 修复模态框 ${modal.id || `modal-${index}`} 失败:`, error);
            }
        });
    }

    /**
     * 修复模态框属性
     */
    function fixModalAttributes(modal) {
        // 确保模态框有正确的属性
        if (!modal.getAttribute('tabindex')) {
            modal.setAttribute('tabindex', '-1');
        }

        if (!modal.getAttribute('aria-hidden')) {
            modal.setAttribute('aria-hidden', 'true');
        }

        // 修复关闭按钮的属性
        const closeButtons = modal.querySelectorAll('[data-dismiss="modal"]');
        closeButtons.forEach(btn => {
            btn.setAttribute('data-bs-dismiss', 'modal');
            btn.removeAttribute('data-dismiss');
        });

        // 修复触发按钮的属性
        const triggers = document.querySelectorAll(`[data-target="#${modal.id}"]`);
        triggers.forEach(trigger => {
            trigger.setAttribute('data-bs-target', `#${modal.id}`);
            trigger.setAttribute('data-bs-toggle', 'modal');
            trigger.removeAttribute('data-target');
            trigger.removeAttribute('data-toggle');
        });
    }

    /**
     * 确保模态框实例存在
     */
    function ensureModalInstance(modal) {
        if (!bootstrap.Modal.getInstance(modal)) {
            new bootstrap.Modal(modal);
        }
    }

    /**
     * 监听模态框的动态变化
     */
    function observeModalChanges() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // 检查新添加的节点是否是模态框
                        if (node.classList && node.classList.contains('modal')) {
                            fixModalAttributes(node);
                            ensureModalInstance(node);
                        }

                        // 检查新添加节点内部的模态框
                        const modals = node.querySelectorAll && node.querySelectorAll('.modal');
                        if (modals) {
                            modals.forEach(modal => {
                                fixModalAttributes(modal);
                                ensureModalInstance(modal);
                            });
                        }
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * 全局模态框工具函数
     */
    window.ModalFix = {
        /**
         * 安全显示模态框
         */
        show: function(modalId) {
            try {
                const modalElement = document.getElementById(modalId);
                if (!modalElement) {
                    console.error(`模态框 ${modalId} 不存在`);
                    return false;
                }

                let modal = bootstrap.Modal.getInstance(modalElement);
                if (!modal) {
                    modal = new bootstrap.Modal(modalElement);
                }

                modal.show();
                return true;
            } catch (error) {
                console.error(`显示模态框 ${modalId} 失败:`, error);
                return false;
            }
        },

        /**
         * 安全隐藏模态框
         */
        hide: function(modalId) {
            try {
                const modalElement = document.getElementById(modalId);
                if (!modalElement) {
                    console.error(`模态框 ${modalId} 不存在`);
                    return false;
                }

                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                return true;
            } catch (error) {
                console.error(`隐藏模态框 ${modalId} 失败:`, error);
                return false;
            }
        },

        /**
         * 关闭所有模态框
         */
        hideAll: function() {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const instance = bootstrap.Modal.getInstance(modal);
                if (instance) {
                    instance.hide();
                }
            });
        }
    };

    // 添加全局错误处理
    window.addEventListener('error', function(event) {
        if (event.message && event.message.includes('modal')) {
            console.warn('检测到模态框相关错误，尝试修复...', event.error);
            // 延迟重新修复所有模态框
            setTimeout(fixExistingModals, 100);
        }
    });

})();
