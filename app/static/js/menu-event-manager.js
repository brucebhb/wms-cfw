/**
 * 菜单事件管理器
 * 解决操作后一级菜单无法点击的问题
 */

(function() {
    'use strict';

    class MenuEventManager {
        constructor() {
            this.isInitialized = false;
            this.eventListeners = new Map();
            this.lastReinitTime = 0;
            this.reinitCooldown = 5000; // 5秒冷却时间
            this.init();
        }

        init() {
            this.setupMenuEventHandlers();
            this.setupEventMonitoring();
            this.setupAutoRecovery();
            console.log('菜单事件管理器已初始化');
        }

        /**
         * 设置菜单事件处理器
         */
        setupMenuEventHandlers() {
            // 移除现有的事件监听器
            this.removeExistingListeners();
            
            // 重新绑定一级菜单事件
            this.bindPrimaryMenuEvents();
            
            // 重新绑定二级菜单事件
            this.bindSecondaryMenuEvents();
            
            // 重新绑定侧边栏切换事件
            this.bindSidebarToggleEvents();
            
            this.isInitialized = true;
        }

        /**
         * 移除现有的事件监听器
         */
        removeExistingListeners() {
            // 移除Bootstrap的collapse事件监听器
            $('.dropdown-toggle').off('click.bs.collapse');

            // 移除自定义的事件监听器
            $(document).off('click.dropdown');
            $(document).off('click.submenu');
            $(document).off('click.submenu-manager');
            $(document).off('click.submenu-toggle');

            console.log('已清理现有的菜单事件监听器');
        }

        /**
         * 绑定一级菜单事件
         */
        bindPrimaryMenuEvents() {
            const self = this;

            // 使用事件委托绑定一级菜单点击事件
            $(document).on('click.menu-manager', '.dropdown-toggle', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const $this = $(this);
                const targetId = $this.attr('href');

                if (!targetId || !targetId.startsWith('#')) {
                    return;
                }

                const $target = $(targetId);
                if ($target.length === 0) {
                    return;
                }

                // 先关闭其他展开的菜单
                $('.dropdown-toggle').not($this).each(function() {
                    const otherTargetId = $(this).attr('href');
                    const $otherTarget = $(otherTargetId);
                    if ($otherTarget.hasClass('show')) {
                        $otherTarget.removeClass('show');
                        $(this).attr('aria-expanded', 'false').addClass('collapsed');
                        $otherTarget.slideUp(200);
                    }
                });

                // 切换当前菜单状态
                self.toggleMenu($this, $target);

                console.log(`一级菜单点击: ${targetId}`);
            });

            console.log('一级菜单事件已绑定');
        }

        /**
         * 切换菜单状态
         */
        toggleMenu($trigger, $target) {
            const isExpanded = $trigger.attr('aria-expanded') === 'true';

            if (isExpanded) {
                // 收起菜单
                $target.removeClass('show');
                $trigger.attr('aria-expanded', 'false');
                $trigger.addClass('collapsed');

                // 添加动画效果
                $target.slideUp(200);
            } else {
                // 展开菜单
                $target.addClass('show');
                $trigger.attr('aria-expanded', 'true');
                $trigger.removeClass('collapsed');

                // 添加动画效果
                $target.slideDown(200);
            }

            // 保存状态
            this.saveMenuState($trigger.attr('href'), !isExpanded);
        }

        /**
         * 保存菜单状态
         */
        saveMenuState(menuId, isExpanded) {
            try {
                const menuStates = JSON.parse(localStorage.getItem('menuStates') || '{}');
                menuStates[menuId] = isExpanded;
                localStorage.setItem('menuStates', JSON.stringify(menuStates));
            } catch (e) {
                console.warn('保存菜单状态失败:', e);
            }
        }

        /**
         * 恢复菜单状态
         */
        restoreMenuStates() {
            try {
                const menuStates = JSON.parse(localStorage.getItem('menuStates') || '{}');

                Object.keys(menuStates).forEach(menuId => {
                    const isExpanded = menuStates[menuId];
                    const $trigger = $(`a[href="${menuId}"]`);
                    const $target = $(menuId);

                    if ($trigger.length && $target.length) {
                        if (isExpanded) {
                            $target.addClass('show');
                            $trigger.attr('aria-expanded', 'true').removeClass('collapsed');
                            $target.show(); // 确保可见
                        } else {
                            $target.removeClass('show');
                            $trigger.attr('aria-expanded', 'false').addClass('collapsed');
                            $target.hide(); // 确保隐藏
                        }
                    }
                });

                console.log('菜单状态已恢复');
            } catch (e) {
                console.warn('恢复菜单状态失败:', e);
            }
        }

        /**
         * 绑定二级菜单事件
         */
        bindSecondaryMenuEvents() {
            const self = this;

            // 使用事件委托绑定二级菜单事件（仓库管理菜单）
            $(document).on('click.submenu-manager', '.submenu-header', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const $this = $(this);
                const targetId = $this.data('target');
                const $target = $('#' + targetId);

                if ($target.length === 0) {
                    return;
                }

                // 切换二级菜单状态
                self.toggleSubmenu($this, $target, targetId);

                console.log(`二级菜单点击: ${targetId}`);
            });

            // 绑定统计报表菜单的折叠事件
            $(document).on('click.submenu-toggle', '.submenu-toggle', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const $this = $(this);
                const $parentLi = $this.closest('li.has-submenu');
                const $submenu = $parentLi.find('.submenu');
                const $arrow = $this.find('.submenu-arrow');

                if ($submenu.length === 0) {
                    return;
                }

                // 切换显示状态
                if ($submenu.is(':visible')) {
                    $submenu.slideUp(200);
                    $arrow.removeClass('fa-chevron-up').addClass('fa-chevron-down');
                    $parentLi.removeClass('open');
                } else {
                    $submenu.slideDown(200);
                    $arrow.removeClass('fa-chevron-down').addClass('fa-chevron-up');
                    $parentLi.addClass('open');
                }

                console.log('统计报表菜单切换');
            });

            console.log('二级菜单事件已绑定');
        }

        /**
         * 切换二级菜单状态
         */
        toggleSubmenu($trigger, $target, targetId) {
            const isCollapsed = $target.hasClass('collapsed');
            
            if (isCollapsed) {
                $target.removeClass('collapsed');
                $trigger.removeClass('collapsed');
            } else {
                $target.addClass('collapsed');
                $trigger.addClass('collapsed');
            }
            
            // 保存二级菜单状态
            this.saveSubmenuState(targetId, !isCollapsed);
        }

        /**
         * 保存二级菜单状态
         */
        saveSubmenuState(targetId, isCollapsed) {
            try {
                const submenuStates = JSON.parse(localStorage.getItem('submenuStates') || '{}');
                submenuStates[targetId] = isCollapsed ? 'collapsed' : 'expanded';
                localStorage.setItem('submenuStates', JSON.stringify(submenuStates));
            } catch (e) {
                console.warn('保存二级菜单状态失败:', e);
            }
        }

        /**
         * 绑定侧边栏切换事件
         */
        bindSidebarToggleEvents() {
            // 先移除现有的事件监听器
            $(document).off('click.sidebar-manager', '#sidebarCollapse');
            $(document).off('click.sidebar-manager', '#sidebar-toggler');

            // 顶部切换按钮
            $(document).on('click.sidebar-manager', '#sidebarCollapse', function(e) {
                e.preventDefault();
                e.stopPropagation();

                $('#sidebar').toggleClass('active');
                $('#content').toggleClass('active');

                // 同步底部箭头图标
                const isActive = $('#sidebar').hasClass('active');
                const $icon = $('#sidebar-toggler i');

                if (isActive) {
                    $icon.removeClass('fa-angle-left').addClass('fa-angle-right');
                    localStorage.setItem('sidebarState', 'collapsed');
                } else {
                    $icon.removeClass('fa-angle-right').addClass('fa-angle-left');
                    localStorage.setItem('sidebarState', 'expanded');
                }

                console.log('侧边栏状态已切换 (顶部按钮)');
            });
            
            // 底部切换按钮
            $(document).on('click.sidebar-manager', '#sidebar-toggler', function(e) {
                e.preventDefault();
                $('#sidebar').toggleClass('active');
                $('#content').toggleClass('active');
                
                const isActive = $('#sidebar').hasClass('active');
                const $icon = $(this).find('i');
                
                if (isActive) {
                    $icon.removeClass('fa-angle-left').addClass('fa-angle-right');
                    localStorage.setItem('sidebarState', 'collapsed');
                } else {
                    $icon.removeClass('fa-angle-right').addClass('fa-angle-left');
                    localStorage.setItem('sidebarState', 'expanded');
                }
                
                console.log('侧边栏状态已切换 (底部按钮)');
            });
            
            console.log('侧边栏切换事件已绑定');
        }

        /**
         * 设置事件监控
         */
        setupEventMonitoring() {
            const self = this;
            
            // 监控DOM变化
            const observer = new MutationObserver(function(mutations) {
                let shouldReinit = false;
                
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        // 检查是否有新的菜单元素添加
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1 && 
                                (node.classList.contains('dropdown-toggle') || 
                                 node.querySelector('.dropdown-toggle'))) {
                                shouldReinit = true;
                            }
                        });
                    }
                });
                
                if (shouldReinit) {
                    setTimeout(() => {
                        self.reinitialize();
                    }, 100);
                }
            });
            
            // 开始观察
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            console.log('DOM变化监控已启动');
        }

        /**
         * 设置自动恢复机制
         */
        setupAutoRecovery() {
            const self = this;

            // 定期检查菜单事件是否正常（降低频率）
            setInterval(() => {
                self.checkMenuHealth();
            }, 60000); // 每60秒检查一次

            // 页面获得焦点时检查（添加防抖）
            let focusTimeout;
            window.addEventListener('focus', () => {
                clearTimeout(focusTimeout);
                focusTimeout = setTimeout(() => {
                    self.checkMenuHealth();
                }, 2000); // 延长到2秒
            });

            // 监听特定的用户操作（添加防抖）
            let ajaxTimeout;
            $(document).on('ajaxComplete', () => {
                clearTimeout(ajaxTimeout);
                ajaxTimeout = setTimeout(() => {
                    self.checkMenuHealth();
                }, 3000); // 延长到3秒
            });

            console.log('自动恢复机制已启动');
        }

        /**
         * 检查菜单健康状态
         */
        checkMenuHealth() {
            const $dropdownToggles = $('.dropdown-toggle');

            if ($dropdownToggles.length === 0) {
                return; // 没有菜单元素
            }

            // 检查是否有我们的事件监听器
            let hasOurEventListeners = false;

            // 检查document上是否有我们绑定的事件
            const documentEvents = $._data(document, 'events') || {};
            if (documentEvents.click) {
                documentEvents.click.forEach(handler => {
                    if (handler.namespace === 'menu-manager') {
                        hasOurEventListeners = true;
                    }
                });
            }

            // 如果没有我们的事件监听器，重新初始化
            if (!hasOurEventListeners && this.isInitialized) {
                console.warn('检测到菜单事件丢失，正在重新初始化...');
                this.reinitialize();
            }
        }

        /**
         * 重新初始化
         */
        reinitialize() {
            const now = Date.now();

            // 检查冷却时间
            if (now - this.lastReinitTime < this.reinitCooldown) {
                console.log('重新初始化冷却中，跳过本次操作');
                return;
            }

            console.log('重新初始化菜单事件管理器...');
            this.lastReinitTime = now;

            this.setupMenuEventHandlers();
            this.restoreMenuStates();

            // 显示恢复提示
            if (typeof showSuccess === 'function') {
                showSuccess('🔧 菜单功能已自动恢复', { duration: 2000 });
            }
        }

        /**
         * 手动重新初始化（供外部调用）
         */
        manualReinit() {
            this.reinitialize();
            console.log('手动重新初始化完成');
        }

        /**
         * 清理资源
         */
        cleanup() {
            // 移除所有事件监听器
            $(document).off('.menu-manager');
            $(document).off('.submenu-manager');
            $(document).off('.sidebar-manager');
            
            this.eventListeners.clear();
            this.isInitialized = false;
            
            console.log('菜单事件管理器已清理');
        }
    }

    // 页面加载完成后初始化
    $(document).ready(function() {
        window.menuEventManager = new MenuEventManager();
        
        // 添加键盘快捷键：Ctrl+Shift+R 重新初始化菜单
        $(document).on('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'R') {
                e.preventDefault();
                window.menuEventManager.manualReinit();
                alert('菜单事件已手动重新初始化');
            }
        });
    });

    // 页面卸载时清理
    $(window).on('beforeunload', function() {
        if (window.menuEventManager) {
            window.menuEventManager.cleanup();
        }
    });

    // 导出到全局
    window.MenuEventManager = MenuEventManager;

})();
