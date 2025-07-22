/**
 * 货量报表仪表板 JavaScript
 */

class CargoVolumeDashboard {
    constructor() {
        this.currentPeriod = 'day';
        this.charts = {};
        this.loginPromptShown = false;
        this.init();
    }

    init() {
        this.initTimeSelectors();
        this.bindEvents();
        this.updateInitialPeriodLabels(); // 先显示基本的日期信息
        this.showInitialContent(); // 先显示基本内容
        this.loadData(); // 异步加载数据
        this.updateLastUpdateTime();

        // 每5分钟自动刷新数据
        setInterval(() => {
            this.loadData();
        }, 5 * 60 * 1000);
    }

    showInitialContent() {
        // 显示基本的页面结构，避免白屏
        this.updateLastUpdateTime();

        // 显示默认的空状态卡片
        this.showDefaultCards();
    }

    showDefaultCards() {
        // 显示默认的仓库卡片，避免页面空白
        const defaultWarehouseData = [
            { warehouse_id: 1, warehouse_name: '平湖仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 2, warehouse_name: '昆山仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 3, warehouse_name: '成都仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 4, warehouse_name: '凭祥北投仓', today_count: 0, today_pallets: 0, today_packages: 0 }
        ];

        this.updateWarehouseCards(defaultWarehouseData);
    }

    initTimeSelectors() {
        // 初始化年份选项
        this.initYearOptions();

        // 初始化默认日期
        this.initDefaultDates();

        // 初始化周次选项
        this.initWeekOptions();

        // 初始化月份选择器
        this.initMonthInputs();

        // 显示默认的时间选择器
        this.showTimeSelector('day');
    }

    initYearOptions() {
        const currentYear = new Date().getFullYear();
        const startYear = currentYear - 5;
        const endYear = currentYear + 1;

        const yearSelectors = [
            'weekYear', 'yearStartYear', 'yearEndYear'
        ];

        yearSelectors.forEach(selectorId => {
            const selector = document.getElementById(selectorId);
            if (selector) {
                selector.innerHTML = '';
                for (let year = startYear; year <= endYear; year++) {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year + '年';
                    if (year === currentYear) {
                        option.selected = true;
                    }
                    selector.appendChild(option);
                }
            }
        });
    }

    initDefaultDates() {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        // 设置日期选择器默认值
        const dayStartDate = document.getElementById('dayStartDate');
        const dayEndDate = document.getElementById('dayEndDate');

        if (dayStartDate) {
            dayStartDate.value = yesterday.toISOString().split('T')[0];
        }
        if (dayEndDate) {
            dayEndDate.value = today.toISOString().split('T')[0];
        }

        // 设置周选择器默认值（本周）
        this.setThisWeek();

        // 月份选择器现在使用input[type="month"]，在initMonthInputs中初始化
    }

    initWeekOptions() {
        // 初始化年份选项
        this.initYearOptions();

        // 绑定周选择器事件
        this.bindWeekSelectors();

        // 绑定快捷按钮事件
        this.bindWeekQuickButtons();

        // 设置默认值（本周）
        this.setThisWeek();
    }

    initYearOptions() {
        const currentYear = new Date().getFullYear();
        const years = [];

        // 生成前后3年的年份选项
        for (let i = currentYear - 3; i <= currentYear + 1; i++) {
            years.push(i);
        }

        // 填充第一周年份选项
        const weekFirstYear = document.getElementById('weekFirstYear');
        if (weekFirstYear) {
            weekFirstYear.innerHTML = '';
            years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year + '年';
                if (year === currentYear) option.selected = true;
                weekFirstYear.appendChild(option);
            });
        }

        // 填充第二周年份选项
        const weekSecondYear = document.getElementById('weekSecondYear');
        if (weekSecondYear) {
            weekSecondYear.innerHTML = '';
            years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year + '年';
                if (year === currentYear) option.selected = true;
                weekSecondYear.appendChild(option);
            });
        }

        // 填充年对比的年份选项
        ['yearStartYear', 'yearEndYear'].forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.innerHTML = '';
                years.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year + '年';
                    if (year === currentYear) option.selected = true;
                    select.appendChild(option);
                });
            }
        });
    }

    initMonthInputs() {
        // 初始化自定义月份选择器
        this.initCustomMonthPicker();
    }

    initCustomMonthPicker() {
        const currentDate = new Date();
        const currentYear = currentDate.getFullYear();
        const currentMonth = currentDate.getMonth() + 1;

        // 初始化选择器状态
        this.monthPickerState = {
            startYear: currentYear,
            endYear: currentYear,
            startMonth: null,  // 初始为null，表示未选择
            endMonth: null,    // 初始为null，表示未选择
            isOpen: false,
            startSelected: false,
            endSelected: false
        };

        // 绑定事件
        this.bindMonthPickerEvents();

        // 初始化显示
        this.updateMonthRangeDisplay();
    }

    bindMonthPickerEvents() {
        const monthRangeInput = document.getElementById('monthRangeInput');
        const monthPickerModal = document.getElementById('monthPickerModal');

        // 点击输入框显示选择器
        if (monthRangeInput) {
            monthRangeInput.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showMonthPicker();
            });
        }

        // 年份切换按钮
        document.getElementById('startYearPrev')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.monthPickerState.startYear--;
            this.updateMonthGrid('start');
        });

        document.getElementById('startYearNext')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.monthPickerState.startYear++;
            this.updateMonthGrid('start');
        });

        document.getElementById('endYearPrev')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.monthPickerState.endYear--;
            this.updateMonthGrid('end');
        });

        document.getElementById('endYearNext')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.monthPickerState.endYear++;
            this.updateMonthGrid('end');
        });

        // 确定和取消按钮
        document.getElementById('confirmMonthRange')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.confirmMonthRange();
        });

        document.getElementById('cancelMonthRange')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hideMonthPicker();
        });

        // 点击外部关闭选择器（但只有在没有选择或已完成选择时才关闭）
        document.addEventListener('click', (e) => {
            if (this.monthPickerState.isOpen &&
                !monthPickerModal?.contains(e.target) &&
                !monthRangeInput?.contains(e.target)) {

                console.log('点击外部，当前状态:', this.monthPickerState);

                // 只有在没有开始选择或已经完成选择时才允许点击外部关闭
                const noSelection = !this.monthPickerState.startSelected && !this.monthPickerState.endSelected;
                const bothSelected = this.monthPickerState.startSelected && this.monthPickerState.endSelected;

                if (noSelection || bothSelected) {
                    console.log('允许关闭选择器');
                    this.hideMonthPicker();
                } else {
                    console.log('阻止关闭选择器，需要完成选择');
                }
            }
        });
    }

    showMonthPicker() {
        const monthPickerModal = document.getElementById('monthPickerModal');
        const monthRangeInput = document.getElementById('monthRangeInput');

        if (monthPickerModal && monthRangeInput) {
            // 重置选择状态
            this.monthPickerState.startSelected = false;
            this.monthPickerState.endSelected = false;
            this.monthPickerState.startMonth = null;
            this.monthPickerState.endMonth = null;

            // 定位弹出框
            const inputRect = monthRangeInput.getBoundingClientRect();
            monthPickerModal.style.top = (inputRect.bottom + 5) + 'px';
            monthPickerModal.style.left = inputRect.left + 'px';
            monthPickerModal.style.display = 'block';

            this.monthPickerState.isOpen = true;

            // 更新显示
            this.updateMonthGrid('start');
            this.updateMonthGrid('end');
            this.updateConfirmButton();
        }
    }

    hideMonthPicker() {
        const monthPickerModal = document.getElementById('monthPickerModal');
        if (monthPickerModal) {
            monthPickerModal.style.display = 'none';
            this.monthPickerState.isOpen = false;
        }
    }

    updateMonthGrid(type) {
        const year = this.monthPickerState[type + 'Year'];
        const selectedMonth = this.monthPickerState[type + 'Month'];

        // 更新年份显示
        const yearDisplay = document.getElementById(type + 'YearDisplay');
        if (yearDisplay) {
            yearDisplay.textContent = year + '年';
        }

        // 更新月份网格
        const monthGrid = document.getElementById(type + 'MonthGrid');
        if (monthGrid) {
            monthGrid.innerHTML = '';

            for (let month = 1; month <= 12; month++) {
                const monthBtn = document.createElement('div');
                monthBtn.className = 'col-3 mb-1';  // 改为4列布局

                const btn = document.createElement('button');
                const isSelected = month === selectedMonth && this.monthPickerState[type + 'Selected'];
                btn.className = `btn btn-sm w-100 py-0 ${isSelected ? (type === 'start' ? 'btn-primary' : 'btn-success') : 'btn-outline-secondary'}`;
                btn.style.fontSize = '11px';
                btn.textContent = month + '月';
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();  // 阻止事件冒泡
                    this.selectMonth(type, year, month);
                });

                monthBtn.appendChild(btn);
                monthGrid.appendChild(monthBtn);
            }
        }
    }

    selectMonth(type, year, month) {
        console.log(`选择月份: ${type} - ${year}年${month}月`);

        this.monthPickerState[type + 'Year'] = year;
        this.monthPickerState[type + 'Month'] = month;
        this.monthPickerState[type + 'Selected'] = true;

        // 更新网格显示
        this.updateMonthGrid(type);

        // 检查是否两个月份都已选择，更新确定按钮状态
        this.updateConfirmButton();

        console.log('当前状态:', this.monthPickerState);
    }

    updateConfirmButton() {
        const confirmBtn = document.getElementById('confirmMonthRange');
        if (confirmBtn) {
            const bothSelected = this.monthPickerState.startSelected && this.monthPickerState.endSelected;
            confirmBtn.disabled = !bothSelected;

            if (bothSelected) {
                confirmBtn.className = 'btn btn-sm btn-success me-2 py-1';
            } else {
                confirmBtn.className = 'btn btn-sm btn-secondary me-2 py-1';
            }
        }
    }

    confirmMonthRange() {
        // 检查是否两个月份都已选择
        if (!this.monthPickerState.startSelected || !this.monthPickerState.endSelected) {
            alert('请先选择起始月份和结束月份');
            return;
        }

        const startDate = new Date(this.monthPickerState.startYear, this.monthPickerState.startMonth - 1);
        const endDate = new Date(this.monthPickerState.endYear, this.monthPickerState.endMonth - 1);

        // 验证范围
        if (startDate > endDate) {
            alert('起始月份不能晚于结束月份');
            return;
        }

        const monthDiff = (endDate.getFullYear() - startDate.getFullYear()) * 12 +
                         (endDate.getMonth() - startDate.getMonth()) + 1;

        if (monthDiff > 12) {
            alert('月份范围不能超过12个月');
            return;
        }

        this.updateMonthRangeDisplay();
        this.hideMonthPicker();
    }

    updateMonthRangeDisplay() {
        const monthRangeInput = document.getElementById('monthRangeInput');
        const monthRangeDisplay = document.getElementById('monthRangeDisplay');

        // 只有两个月份都选择了才更新显示
        if (this.monthPickerState.startSelected && this.monthPickerState.endSelected) {
            const startText = `${this.monthPickerState.startYear}年${this.monthPickerState.startMonth}月`;
            const endText = `${this.monthPickerState.endYear}年${this.monthPickerState.endMonth}月`;

            if (monthRangeInput) {
                monthRangeInput.value = `${startText} - ${endText}`;
            }

            if (monthRangeDisplay) {
                const startDate = new Date(this.monthPickerState.startYear, this.monthPickerState.startMonth - 1);
                const endDate = new Date(this.monthPickerState.endYear, this.monthPickerState.endMonth - 1);
                const monthDiff = (endDate.getFullYear() - startDate.getFullYear()) * 12 +
                                 (endDate.getMonth() - startDate.getMonth()) + 1;

                monthRangeDisplay.textContent = `${startText} 至 ${endText}，共${monthDiff}个月`;
                monthRangeDisplay.className = 'text-success';
            }
        } else {
            // 如果没有完全选择，显示提示信息
            if (monthRangeInput) {
                monthRangeInput.value = '';
                monthRangeInput.placeholder = '点击选择月份范围';
            }

            if (monthRangeDisplay) {
                monthRangeDisplay.textContent = '请选择完整的月份范围';
                monthRangeDisplay.className = 'text-warning';
            }
        }
    }

    bindWeekSelectors() {
        // 第一周选择器事件
        const weekFirstYear = document.getElementById('weekFirstYear');
        const weekFirstMonth = document.getElementById('weekFirstMonth');
        const weekFirstWeek = document.getElementById('weekFirstWeek');

        if (weekFirstYear && weekFirstMonth && weekFirstWeek) {
            const updateFirstWeeks = () => {
                const year = parseInt(weekFirstYear.value);
                const month = parseInt(weekFirstMonth.value);
                this.updateWeekOptions(year, month, 'weekFirstWeek', 'weekFirstRange');
            };

            weekFirstYear.addEventListener('change', updateFirstWeeks);
            weekFirstMonth.addEventListener('change', updateFirstWeeks);
            weekFirstWeek.addEventListener('change', () => {
                this.updateWeekDateRange('weekFirstYear', 'weekFirstMonth', 'weekFirstWeek', 'weekFirstRange');
            });
        }

        // 第二周选择器事件
        const weekSecondYear = document.getElementById('weekSecondYear');
        const weekSecondMonth = document.getElementById('weekSecondMonth');
        const weekSecondWeek = document.getElementById('weekSecondWeek');

        if (weekSecondYear && weekSecondMonth && weekSecondWeek) {
            const updateSecondWeeks = () => {
                const year = parseInt(weekSecondYear.value);
                const month = parseInt(weekSecondMonth.value);
                this.updateWeekOptions(year, month, 'weekSecondWeek', 'weekSecondRange');
            };

            weekSecondYear.addEventListener('change', updateSecondWeeks);
            weekSecondMonth.addEventListener('change', updateSecondWeeks);
            weekSecondWeek.addEventListener('change', () => {
                this.updateWeekDateRange('weekSecondYear', 'weekSecondMonth', 'weekSecondWeek', 'weekSecondRange');
            });
        }
    }

    bindSecondWeekToggle() {
        // 第二周现在总是显示，不需要开关逻辑
        // 初始化第二周的周次选项
        const weekSecondYear = document.getElementById('weekSecondYear');
        const weekSecondMonth = document.getElementById('weekSecondMonth');
        if (weekSecondYear && weekSecondMonth) {
            const year = parseInt(weekSecondYear.value);
            const month = parseInt(weekSecondMonth.value);
            this.updateWeekOptions(year, month, 'weekSecondWeek', 'weekSecondRange');
        }
    }

    updateWeekOptions(year, month, weekSelectId, rangeDisplayId) {
        const weekSelect = document.getElementById(weekSelectId);
        if (!weekSelect) return;

        // 清空现有选项
        weekSelect.innerHTML = '';

        // 计算该月的周次
        const weeks = this.getWeeksInMonth(year, month);

        weeks.forEach((week, index) => {
            const option = document.createElement('option');
            option.value = index + 1;
            option.textContent = `第${index + 1}周`;
            option.dataset.startDate = this.formatDate(week.start);
            option.dataset.endDate = this.formatDate(week.end);
            weekSelect.appendChild(option);
        });

        // 默认选择第一周
        if (weekSelect.options.length > 0) {
            weekSelect.selectedIndex = 0;
            this.updateWeekDateRange(
                weekSelectId.replace('Week', 'Year'),
                weekSelectId.replace('Week', 'Month'),
                weekSelectId,
                rangeDisplayId
            );
        }
    }

    updateWeekDateRange(year, month, weekNumber, rangeId) {
        const rangeDisplay = document.getElementById(rangeId);
        if (!rangeDisplay || !weekNumber) return;

        // 如果传入的是字符串ID（兼容旧的调用方式）
        if (typeof year === 'string') {
            const yearElement = document.getElementById(year);
            const monthElement = document.getElementById(month);
            const weekElement = document.getElementById(weekNumber);

            if (!yearElement || !monthElement || !weekElement || !weekElement.selectedOptions[0]) return;

            const selectedOption = weekElement.selectedOptions[0];
            const startDate = selectedOption.dataset.startDate;
            const endDate = selectedOption.dataset.endDate;

            if (startDate && endDate) {
                rangeDisplay.textContent = `${startDate} 至 ${endDate}`;
            }
            return;
        }

        // 新的调用方式：直接传递数值
        const weeks = this.getWeeksInMonth(year, month);
        const weekIndex = parseInt(weekNumber) - 1;

        if (weekIndex >= 0 && weekIndex < weeks.length) {
            const week = weeks[weekIndex];
            const startDate = this.formatDate(week.start);
            const endDate = this.formatDate(week.end);
            rangeDisplay.textContent = `${startDate} 至 ${endDate}`;
        }
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    getWeeksInMonth(year, month) {
        const weeks = [];
        const firstDay = new Date(year, month - 1, 1);
        const lastDay = new Date(year, month, 0);

        // 找到第一周的开始（周一）
        let currentDate = new Date(firstDay);
        const dayOfWeek = currentDate.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        currentDate.setDate(currentDate.getDate() - daysToMonday);

        while (currentDate <= lastDay) {
            const weekStart = new Date(currentDate);
            const weekEnd = new Date(currentDate);
            weekEnd.setDate(weekEnd.getDate() + 6);

            // 确保周结束不超过月末
            if (weekEnd > lastDay) {
                weekEnd.setTime(lastDay.getTime());
            }

            // 只有当周的开始或结束在当月内时才添加
            if (weekStart.getMonth() === month - 1 || weekEnd.getMonth() === month - 1) {
                weeks.push({
                    start: new Date(weekStart),
                    end: new Date(weekEnd),
                    startShort: this.formatDateShort(weekStart),
                    endShort: this.formatDateShort(weekEnd)
                });
            }

            currentDate.setDate(currentDate.getDate() + 7);
        }

        return weeks;
    }

    formatDateShort(date) {
        return `${date.getMonth() + 1}/${date.getDate()}`;
    }

    bindWeekQuickButtons() {
        // 本周按钮
        const setThisWeekBtn = document.getElementById('setThisWeekBtn');
        if (setThisWeekBtn) {
            setThisWeekBtn.addEventListener('click', () => this.setThisWeek());
        }

        // 上周按钮
        const setLastWeekBtn = document.getElementById('setLastWeekBtn');
        if (setLastWeekBtn) {
            setLastWeekBtn.addEventListener('click', () => this.setLastWeek());
        }

        // 本周vs上周按钮
        const setThisLastWeekBtn = document.getElementById('setThisLastWeekBtn');
        if (setThisLastWeekBtn) {
            setThisLastWeekBtn.addEventListener('click', () => this.setThisVsLastWeek());
        }
    }

    setThisWeek() {
        const today = new Date();
        const currentYear = today.getFullYear();
        const currentMonth = today.getMonth() + 1;

        // 设置第一周的年份和月份
        const weekFirstYear = document.getElementById('weekFirstYear');
        const weekFirstMonth = document.getElementById('weekFirstMonth');

        if (weekFirstYear) {
            weekFirstYear.value = currentYear;
        }
        if (weekFirstMonth) {
            weekFirstMonth.value = currentMonth;
        }

        // 更新周次选项
        this.updateWeekOptions(currentYear, currentMonth, 'weekFirstWeek', 'weekFirstRange');

        // 找到本周是第几周
        const weekNumber = this.getCurrentWeekNumber(today, currentYear, currentMonth);
        const weekFirstWeek = document.getElementById('weekFirstWeek');
        if (weekFirstWeek && weekNumber > 0) {
            weekFirstWeek.value = weekNumber;
            this.updateWeekDateRange('weekFirstYear', 'weekFirstMonth', 'weekFirstWeek', 'weekFirstRange');
        }

        // 第二周现在总是显示，不需要关闭
    }

    setLastWeek() {
        const today = new Date();
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);

        const lastWeekYear = lastWeek.getFullYear();
        const lastWeekMonth = lastWeek.getMonth() + 1;

        // 设置第一周的年份和月份
        const weekFirstYear = document.getElementById('weekFirstYear');
        const weekFirstMonth = document.getElementById('weekFirstMonth');

        if (weekFirstYear) {
            weekFirstYear.value = lastWeekYear;
        }
        if (weekFirstMonth) {
            weekFirstMonth.value = lastWeekMonth;
        }

        // 更新周次选项
        this.updateWeekOptions(lastWeekYear, lastWeekMonth, 'weekFirstWeek', 'weekFirstRange');

        // 找到上周是第几周
        const weekNumber = this.getCurrentWeekNumber(lastWeek, lastWeekYear, lastWeekMonth);
        const weekFirstWeek = document.getElementById('weekFirstWeek');
        if (weekFirstWeek && weekNumber > 0) {
            weekFirstWeek.value = weekNumber;
            this.updateWeekDateRange('weekFirstYear', 'weekFirstMonth', 'weekFirstWeek', 'weekFirstRange');
        }

        // 第二周现在总是显示，不需要关闭
    }

    setThisVsLastWeek() {
        const today = new Date();
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);

        const currentYear = today.getFullYear();
        const currentMonth = today.getMonth() + 1;
        const lastWeekYear = lastWeek.getFullYear();
        const lastWeekMonth = lastWeek.getMonth() + 1;

        // 设置第一周（上周）
        const weekFirstYear = document.getElementById('weekFirstYear');
        const weekFirstMonth = document.getElementById('weekFirstMonth');

        if (weekFirstYear) {
            weekFirstYear.value = lastWeekYear;
        }
        if (weekFirstMonth) {
            weekFirstMonth.value = lastWeekMonth;
        }

        this.updateWeekOptions(lastWeekYear, lastWeekMonth, 'weekFirstWeek', 'weekFirstRange');

        const lastWeekNumber = this.getCurrentWeekNumber(lastWeek, lastWeekYear, lastWeekMonth);
        const weekFirstWeek = document.getElementById('weekFirstWeek');
        if (weekFirstWeek && lastWeekNumber > 0) {
            weekFirstWeek.value = lastWeekNumber;
            this.updateWeekDateRange('weekFirstYear', 'weekFirstMonth', 'weekFirstWeek', 'weekFirstRange');
        }

        // 设置第二周（本周）
        const weekSecondYear = document.getElementById('weekSecondYear');
        const weekSecondMonth = document.getElementById('weekSecondMonth');

        if (weekSecondYear) {
            weekSecondYear.value = currentYear;
        }
        if (weekSecondMonth) {
            weekSecondMonth.value = currentMonth;
        }

        this.updateWeekOptions(currentYear, currentMonth, 'weekSecondWeek', 'weekSecondRange');

        const currentWeekNumber = this.getCurrentWeekNumber(today, currentYear, currentMonth);
        const weekSecondWeek = document.getElementById('weekSecondWeek');
        if (weekSecondWeek && currentWeekNumber > 0) {
            weekSecondWeek.value = currentWeekNumber;
            this.updateWeekDateRange('weekSecondYear', 'weekSecondMonth', 'weekSecondWeek', 'weekSecondRange');
        }
    }

    getCurrentWeekNumber(date, year, month) {
        const weeks = this.getWeeksInMonth(year, month);
        const dayOfWeek = date.getDay();
        const mondayOffset = dayOfWeek === 0 ? 6 : dayOfWeek - 1;

        const monday = new Date(date);
        monday.setDate(date.getDate() - mondayOffset);

        const mondayStr = this.formatDateShort(monday);

        for (let i = 0; i < weeks.length; i++) {
            if (weeks[i].start === mondayStr) {
                return i + 1;
            }
        }

        return 1; // 默认返回第一周
    }

    // 移除enableSecondWeek和disableSecondWeek方法，因为第二周现在总是显示

    showTimeSelector(period) {
        console.log('显示时间选择器:', period);
        // 隐藏所有时间选择器
        const selectors = ['daySelection', 'weekSelection', 'monthSelection', 'yearSelection'];
        selectors.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'none';
                console.log('隐藏选择器:', id);
            }
        });

        // 显示对应的时间选择器
        const targetSelector = document.getElementById(period + 'Selection');
        console.log('目标选择器:', period + 'Selection', '元素存在:', !!targetSelector);
        if (targetSelector) {
            targetSelector.style.display = 'block';
            console.log('显示选择器:', period + 'Selection');
        } else {
            console.error('未找到目标选择器:', period + 'Selection');
        }

        // 隐藏查询结果
        const queryResultArea = document.getElementById('queryResultArea');
        if (queryResultArea) {
            queryResultArea.style.display = 'none';
        }
    }

    bindEvents() {
        // 时间维度选择器
        document.querySelectorAll('input[name="timePeriod"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentPeriod = e.target.value;
                this.showTimeSelector(e.target.value);
                this.updateComparisonTitle();
            });
        });

        // 查询按钮事件
        this.bindQueryEvents();

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadData();
        });
    }



    updateLastUpdateTime() {
        const now = new Date();
        const timeStr = now.toLocaleString('zh-CN');
        document.getElementById('lastUpdateTime').textContent = `最后更新: ${timeStr}`;
    }

    updateComparisonTitle() {
        const titles = {
            'day': '日对比分析',
            'week': '周对比分析',
            'month': '月对比分析',
            'year': '年对比分析'
        };
        document.getElementById('comparisonTitle').textContent = titles[this.currentPeriod] || '对比分析';
    }

    updateInitialPeriodLabels() {
        // 页面加载时立即显示日期信息，不等待数据加载
        this.updatePeriodLabels(null, null);
    }

    updatePeriodLabels(trendsData, comparisonData) {
        const today = new Date();

        // 更新按钮标签显示具体日期
        const dayLabel = document.querySelector('label[for="dayPeriod"]');
        const weekLabel = document.querySelector('label[for="weekPeriod"]');
        const monthLabel = document.querySelector('label[for="monthPeriod"]');
        const yearLabel = document.querySelector('label[for="yearPeriod"]');

        if (dayLabel) {
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            const todayStr = `${today.getMonth() + 1}/${today.getDate()}`;
            const yesterdayStr = `${yesterday.getMonth() + 1}/${yesterday.getDate()}`;
            dayLabel.innerHTML = `日对比<br><small class="text-muted">${yesterdayStr} vs ${todayStr}</small>`;
        }

        if (weekLabel) {
            const monday = new Date(today);
            monday.setDate(today.getDate() - today.getDay() + 1);
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);
            const mondayStr = `${monday.getMonth() + 1}/${monday.getDate()}`;
            const sundayStr = `${sunday.getMonth() + 1}/${sunday.getDate()}`;
            weekLabel.innerHTML = `周对比<br><small class="text-muted">${mondayStr} - ${sundayStr}</small>`;
        }

        if (monthLabel) {
            const monthStr = `${today.getFullYear()}年${today.getMonth() + 1}月`;
            monthLabel.innerHTML = `月对比<br><small class="text-muted">${monthStr}（至${today.getDate()}日）</small>`;
        }

        if (yearLabel) {
            const yearStr = `${today.getFullYear()}年`;
            const monthStr = `${today.getMonth() + 1}月`;
            yearLabel.innerHTML = `年对比<br><small class="text-muted">${yearStr}（至${monthStr}）</small>`;
        }
    }

    async loadData() {
        try {
            console.log('开始加载数据...');

            // 先单独测试仓库数据
            const warehouseData = await this.fetchWarehouseData();
            console.log('仓库数据加载完成:', warehouseData);

            // 更新仓库卡片
            this.updateWarehouseCards(warehouseData);

            // 加载其他数据（使用超时控制）
            const [overviewData, comparisonData] = await Promise.allSettled([
                this.fetchWithTimeout(this.fetchOverviewData(), 10000),
                this.fetchWithTimeout(this.fetchComparisonData(), 10000)
            ]);

            // 更新UI（即使部分数据加载失败也要显示已有数据）
            if (overviewData.status === 'fulfilled') {
                this.updateOverviewCards(overviewData.value);
            } else {
                console.warn('总览数据加载失败:', overviewData.reason);
            }

            if (comparisonData.status === 'fulfilled') {
                this.updateComparisonCharts(comparisonData.value);
            } else {
                console.warn('对比数据加载失败:', comparisonData.reason);
            }

            this.updateLastUpdateTime();

        } catch (error) {
            console.error('数据加载失败:', error);
            // 不显示错误提示，避免影响用户体验
            console.warn('部分数据加载失败，页面将显示默认内容');
        }
    }

    async fetchWithTimeout(promise, timeout = 5000) {
        return Promise.race([
            promise,
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('请求超时')), timeout)
            )
        ]);
    }

    setLoadingState(isLoading) {
        // 移除加载动画，直接更新时间
        if (!isLoading) {
            this.updateLastUpdateTime();
        }
    }

    async fetchOverviewData() {
        try {
            const response = await fetch('/reports/api/cargo_volume/overview');
            if (!response.ok) {
                if (response.status === 401) {
                    this.showLoginRequired();
                    return this.getDefaultOverviewData();
                }
                console.error('总览数据获取失败:', response.status);
                return this.getDefaultOverviewData();
            }
            const result = await response.json();
            if (!result.success) {
                if (result.error_code === 'AUTHENTICATION_REQUIRED') {
                    this.showLoginRequired();
                    return this.getDefaultOverviewData();
                }
                console.error('总览数据业务逻辑失败:', result.message);
                return this.getDefaultOverviewData();
            }
            return result.data;
        } catch (error) {
            console.error('总览数据网络请求失败:', error);
            return this.getDefaultOverviewData();
        }
    }

    getDefaultOverviewData() {
        return {
            today_inbound: { count: 0, pallets: 0, packages: 0 },
            today_outbound: { count: 0, pallets: 0, packages: 0 },
            inventory_stats: { count: 0, pallets: 0, packages: 0 },
            in_transit: { count: 0, pallets: 0, packages: 0 }
        };
    }

    showLoginRequired() {
        // 只显示一次登录提示
        if (this.loginPromptShown) return;
        this.loginPromptShown = true;

        // 创建登录提示横幅
        const banner = document.createElement('div');
        banner.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        banner.style.cssText = `
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        banner.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                <div class="flex-grow-1">
                    <strong>需要登录</strong><br>
                    <small>请先登录系统以查看完整的货量数据</small>
                </div>
                <a href="/auth/login" class="btn btn-warning btn-sm ms-3">
                    <i class="fas fa-sign-in-alt"></i> 立即登录
                </a>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.body.appendChild(banner);

        // 5秒后自动隐藏
        setTimeout(() => {
            if (banner.parentNode) {
                banner.remove();
            }
        }, 8000);
    }

    async fetchTrendsData() {
        const response = await fetch(`/reports/api/cargo_volume/trends?period=${this.currentPeriod}`);
        if (!response.ok) throw new Error('获取趋势数据失败');
        const result = await response.json();
        if (!result.success) throw new Error(result.message);
        return result.data;
    }

    async fetchWarehouseData() {
        try {
            console.log('开始获取仓库数据...');
            const response = await fetch('/reports/api/cargo_volume/warehouse_stats');
            console.log('仓库数据响应状态:', response.status);

            if (!response.ok) {
                if (response.status === 401) {
                    this.showLoginRequired();
                    return this.getDefaultWarehouseData();
                }
                const errorText = await response.text();
                console.error('仓库数据获取失败:', errorText);
                return this.getDefaultWarehouseData();
            }

            const result = await response.json();
            console.log('仓库数据结果:', result);

            if (!result.success) {
                console.error('仓库数据业务逻辑失败:', result.message);
                return this.getDefaultWarehouseData();
            }

            return result.data;
        } catch (error) {
            console.error('仓库数据网络请求失败:', error);
            return this.getDefaultWarehouseData();
        }
    }

    getDefaultWarehouseData() {
        return [
            { warehouse_id: 1, warehouse_name: '平湖仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 2, warehouse_name: '昆山仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 3, warehouse_name: '成都仓', today_count: 0, today_pallets: 0, today_packages: 0 },
            { warehouse_id: 4, warehouse_name: '凭祥北投仓', today_count: 0, today_pallets: 0, today_packages: 0 }
        ];
    }

    async fetchComparisonData() {
        try {
            const response = await fetch(`/reports/api/cargo_volume/comparison?type=${this.currentPeriod}`);
            if (!response.ok) {
                if (response.status === 401) {
                    this.showLoginRequired();
                    return this.getDefaultComparisonData();
                }
                console.error('对比数据获取失败:', response.status);
                return this.getDefaultComparisonData();
            }
            const result = await response.json();
            if (!result.success) {
                console.error('对比数据业务逻辑失败:', result.message);
                return this.getDefaultComparisonData();
            }
            return result.data;
        } catch (error) {
            console.error('对比数据网络请求失败:', error);
            return this.getDefaultComparisonData();
        }
    }

    getDefaultComparisonData() {
        return {
            chart_data: [],
            summary: { total_count: 0, total_pallets: 0, total_packages: 0 }
        };
    }

    updateOverviewCards(data) {
        // 今日进货
        document.getElementById('todayInboundCount').textContent = data.today_inbound.count;
        document.getElementById('todayInboundPallets').textContent = this.formatNumber(data.today_inbound.pallets);
        document.getElementById('todayInboundPackages').textContent = this.formatNumber(data.today_inbound.packages);

        // 今日出货
        document.getElementById('todayOutboundCount').textContent = data.today_outbound.count;
        document.getElementById('todayOutboundPallets').textContent = this.formatNumber(data.today_outbound.pallets);
        document.getElementById('todayOutboundPackages').textContent = this.formatNumber(data.today_outbound.packages);

        // 库存总量
        document.getElementById('inventoryCount').textContent = data.inventory_stats.count;
        document.getElementById('inventoryPallets').textContent = this.formatNumber(data.inventory_stats.pallets);
        document.getElementById('inventoryPackages').textContent = this.formatNumber(data.inventory_stats.packages);

        // 在途货物
        document.getElementById('transitCount').textContent = data.transit_stats.count;
        document.getElementById('transitPallets').textContent = this.formatNumber(data.transit_stats.pallets);
        document.getElementById('transitPackages').textContent = this.formatNumber(data.transit_stats.packages);

        // 更新趋势指示器
        this.updateTrendIndicator('inboundTrend', data.comparison.inbound_growth.count);
        this.updateTrendIndicator('outboundTrend', data.comparison.outbound_growth.count);
    }

    updateTrendIndicator(elementId, growthRate) {
        const element = document.getElementById(elementId);
        const badge = element.querySelector('.badge');
        const icon = badge.querySelector('i');
        
        const absRate = Math.abs(growthRate);
        const rateText = `${growthRate >= 0 ? '+' : ''}${growthRate.toFixed(1)}%`;
        
        if (growthRate > 0) {
            badge.className = 'badge bg-success';
            icon.className = 'fas fa-arrow-up';
        } else if (growthRate < 0) {
            badge.className = 'badge bg-danger';
            icon.className = 'fas fa-arrow-down';
        } else {
            badge.className = 'badge bg-secondary';
            icon.className = 'fas fa-minus';
        }
        
        badge.innerHTML = `<i class="${icon.className}"></i> ${rateText}`;
    }

    updateTrendsCharts(data) {
        if (data.separated) {
            // 分离的数据，创建4个图表
            this.createSeparatedTrendChart('frontendInboundTrendChart', data, 'frontend_inbound', '前端仓进货趋势', '#007bff');
            this.createSeparatedTrendChart('frontendOutboundTrendChart', data, 'frontend_outbound', '前端仓出货趋势', '#28a745');
            this.createSeparatedTrendChart('backendInboundTrendChart', data, 'backend_inbound', '后端仓进货趋势', '#17a2b8');
            this.createSeparatedTrendChart('backendOutboundTrendChart', data, 'backend_outbound', '后端仓出货趋势', '#ffc107');
        } else {
            // 原有的合并数据（向后兼容）
            this.createTrendChart('frontendInboundTrendChart', data, 'inbound', '进货趋势', '#007bff');
            this.createTrendChart('frontendOutboundTrendChart', data, 'outbound', '出货趋势', '#28a745');
        }
    }

    createTrendChart(containerId, data, type, title, color) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // 销毁现有图表
        if (this.charts[containerId]) {
            this.charts[containerId].dispose();
        }

        const chart = echarts.init(container);
        
        // 准备数据
        const xAxisData = [];
        const countData = [];
        const palletsData = [];
        const packagesData = [];

        data.data.forEach((item, index) => {
            if (data.period === 'day') {
                // 日对比：显示"昨天"、"今天"
                xAxisData.push(item.weekday_cn || item.date);
            } else if (data.period === 'week') {
                // 周对比：显示星期
                xAxisData.push(item.weekday_cn || item.date);
            } else if (data.period === 'month') {
                // 自然月显示：日期 + 星期
                const weekday = item.weekday_cn || '';
                const label = `${item.day}日${weekday ? '\n' + weekday : ''}`;
                xAxisData.push(label);
            } else {
                // 年对比：显示月份
                xAxisData.push(item.month_name || item.date);
            }

            // 确保数据存在且有效
            const itemData = item[type] || {};
            countData.push(itemData.count || 0);
            palletsData.push(itemData.pallets || 0);
            packagesData.push(itemData.packages || 0);
        });

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter: function(params) {
                    let result = `${params[0].axisValue}<br/>`;
                    params.forEach(param => {
                        result += `${param.marker}${param.seriesName}: ${param.value}<br/>`;
                    });
                    return result;
                }
            },
            legend: {
                data: ['票数', '板数', '件数'],
                bottom: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: {
                    rotate: data.period === 'month' ? 45 : 0,
                    interval: data.period === 'month' ? 'auto' : 0,
                    fontSize: data.period === 'month' ? 10 : 12
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '票数',
                    position: 'left'
                },
                {
                    type: 'value',
                    name: '板数/件数',
                    position: 'right'
                }
            ],
            series: [
                {
                    name: '票数',
                    type: 'line',
                    data: countData,
                    smooth: true,
                    lineStyle: {
                        color: color,
                        width: 3
                    },
                    itemStyle: {
                        color: color
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: color + '40' },
                                { offset: 1, color: color + '10' }
                            ]
                        }
                    }
                },
                {
                    name: '板数',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: palletsData,
                    itemStyle: {
                        color: color + '80'
                    }
                },
                {
                    name: '件数',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: packagesData,
                    itemStyle: {
                        color: color + '60'
                    }
                }
            ]
        };

        chart.setOption(option);
        this.charts[containerId] = chart;

        // 响应式调整
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }

    createSeparatedTrendChart(containerId, data, type, title, color) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`图表容器 ${containerId} 不存在`);
            return;
        }

        // 销毁已存在的图表
        if (this.charts[containerId]) {
            this.charts[containerId].dispose();
        }

        const chart = echarts.init(container);

        // 准备数据
        const xAxisData = [];
        const countData = [];
        const palletsData = [];
        const packagesData = [];

        data.data.forEach((item, index) => {
            if (data.period === 'day') {
                // 日对比：显示"昨天"、"今天"
                xAxisData.push(item.weekday_cn || item.date);
            } else if (data.period === 'week') {
                // 周对比：显示星期
                xAxisData.push(item.weekday_cn || item.date);
            } else if (data.period === 'month') {
                // 自然月显示：日期 + 星期
                const weekday = item.weekday_cn || '';
                const label = `${item.day}日${weekday ? '\n' + weekday : ''}`;
                xAxisData.push(label);
            } else {
                // 年对比：显示月份
                xAxisData.push(item.month_name || item.date);
            }

            // 确保数据存在且有效
            const itemData = item[type] || {};
            countData.push(itemData.count || 0);
            palletsData.push(itemData.pallets || 0);
            packagesData.push(itemData.packages || 0);
        });

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter: function(params) {
                    let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`;
                    params.forEach(param => {
                        const value = param.value;
                        const unit = param.seriesName.includes('票数') ? '票' :
                                   param.seriesName.includes('托盘') ? '托' : '件';
                        result += `<div style="margin: 2px 0;">
                            <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; margin-right: 5px;"></span>
                            ${param.seriesName}: <strong>${value}${unit}</strong>
                        </div>`;
                    });
                    return result;
                }
            },
            legend: {
                data: ['票数', '托盘数', '包裹数'],
                bottom: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: {
                    rotate: data.period === 'month' ? 45 : 0,
                    interval: data.period === 'month' ? 'auto' : 0,
                    fontSize: data.period === 'month' ? 10 : 12
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '票数',
                    position: 'left'
                },
                {
                    type: 'value',
                    name: '板数/件数',
                    position: 'right'
                }
            ],
            series: [
                {
                    name: '票数',
                    type: 'line',
                    yAxisIndex: 0,
                    data: countData,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 6,
                    lineStyle: {
                        width: 3,
                        color: color
                    },
                    itemStyle: {
                        color: color
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: color + '40' },
                                { offset: 1, color: color + '10' }
                            ]
                        }
                    }
                },
                {
                    name: '托盘数',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: palletsData,
                    itemStyle: {
                        color: color + '80'
                    }
                },
                {
                    name: '包裹数',
                    type: 'bar',
                    yAxisIndex: 1,
                    data: packagesData,
                    itemStyle: {
                        color: color + '60'
                    }
                }
            ]
        };

        chart.setOption(option);
        this.charts[containerId] = chart;

        // 响应式调整
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }

    updateWarehouseStats(data) {
        console.log('🏭 开始更新仓库货量分布，数据:', data);

        const container = document.getElementById('warehouseStatsContainer');
        if (!container) {
            console.error('❌ 未找到 warehouseStatsContainer 元素');
            return;
        }

        console.log('✅ 找到 warehouseStatsContainer 元素');

        let html = '';

        // 使用简化的显示方式，直接显示汇总数据
        if (data.frontend_summary) {
            html += this.createSimpleStatsCard('前端仓汇总', data.frontend_summary, 'primary');
            console.log('📊 添加前端仓汇总');
        }

        if (data.backend_summary) {
            html += this.createSimpleStatsCard('后端仓汇总', data.backend_summary, 'success');
            console.log('📊 添加后端仓汇总');
        }

        // 添加库存统计
        if (data.inventory_stats) {
            html += this.createInventoryStatsCard(data.inventory_stats);
            console.log('📊 添加库存统计');
        }

        console.log('📝 生成的HTML长度:', html.length);
        container.innerHTML = html;
        console.log('✅ 仓库货量分布更新完成');
    }

    createSimpleStatsCard(title, data, colorClass) {
        return `
            <div class="row mb-3">
                <div class="col-12">
                    <div class="card border-${colorClass}">
                        <div class="card-header bg-${colorClass} text-white">
                            <h6 class="mb-0"><i class="fas fa-warehouse me-2"></i>${title}</h6>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-md-3">
                                    <div class="stat-item">
                                        <div class="stat-value text-${colorClass}">${data.inbound?.count || 0}</div>
                                        <div class="stat-label">今日进货票数</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-item">
                                        <div class="stat-value text-${colorClass}">${data.outbound?.count || 0}</div>
                                        <div class="stat-label">今日出货票数</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-item">
                                        <div class="stat-value text-${colorClass}">${this.formatNumber(data.inbound?.pallets || 0)}</div>
                                        <div class="stat-label">进货板数</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-item">
                                        <div class="stat-value text-${colorClass}">${this.formatNumber(data.outbound?.pallets || 0)}</div>
                                        <div class="stat-label">出货板数</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createInventoryStatsCard(data) {
        return `
            <div class="row mb-3">
                <div class="col-12">
                    <div class="card border-info">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fas fa-boxes me-2"></i>库存统计</h6>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-md-4">
                                    <div class="stat-item">
                                        <div class="stat-value text-info">${data.total_count || 0}</div>
                                        <div class="stat-label">总票数</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-item">
                                        <div class="stat-value text-info">${this.formatNumber(data.total_pallets || 0)}</div>
                                        <div class="stat-label">总板数</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-item">
                                        <div class="stat-value text-info">${this.formatNumber(data.total_packages || 0)}</div>
                                        <div class="stat-label">总件数</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createWarehouseGroupCard(title, data, colorClass) {
        return `
            <div class="row mb-3">
                <div class="col-md-6">
                    <div class="warehouse-stat-item border-start border-${colorClass} border-3">
                        <h6 class="text-${colorClass} mb-2">${title} - 进货</h6>
                        <div class="d-flex justify-content-between">
                            <span>票数: <strong>${data.inbound.count}</strong></span>
                            <span>板数: <strong>${this.formatNumber(data.inbound.pallets)}</strong></span>
                            <span>件数: <strong>${this.formatNumber(data.inbound.packages)}</strong></span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="warehouse-stat-item border-start border-${colorClass} border-3">
                        <h6 class="text-${colorClass} mb-2">${title} - 出货</h6>
                        <div class="d-flex justify-content-between">
                            <span>票数: <strong>${data.outbound.count}</strong></span>
                            <span>板数: <strong>${this.formatNumber(data.outbound.pallets)}</strong></span>
                            <span>件数: <strong>${this.formatNumber(data.outbound.packages)}</strong></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createWarehouseCard(warehouse) {
        const typeClass = warehouse.warehouse_type === 'frontend' ? 'primary' : 'success';
        const typeName = warehouse.warehouse_type === 'frontend' ? '前端仓' : '后端仓';
        
        return `
            <div class="col-lg-4 col-md-6 mb-3">
                <div class="card border-0 shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h6 class="card-title mb-0">${warehouse.warehouse_name}</h6>
                            <span class="badge bg-${typeClass} warehouse-type-badge">${typeName}</span>
                        </div>
                        
                        <div class="row text-center">
                            <div class="col-4">
                                <div class="text-primary">
                                    <i class="fas fa-arrow-down"></i>
                                    <div class="mt-1">
                                        <small class="text-muted">进货</small>
                                        <div><strong>${warehouse.inbound.count}</strong></div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="text-success">
                                    <i class="fas fa-arrow-up"></i>
                                    <div class="mt-1">
                                        <small class="text-muted">出货</small>
                                        <div><strong>${warehouse.outbound.count}</strong></div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="text-info">
                                    <i class="fas fa-boxes"></i>
                                    <div class="mt-1">
                                        <small class="text-muted">库存</small>
                                        <div><strong>${warehouse.inventory.count}</strong></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr class="my-2">
                        
                        <div class="row text-center">
                            <div class="col-6">
                                <small class="text-muted">板数: ${this.formatNumber(warehouse.inbound.pallets + warehouse.outbound.pallets)}</small>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">件数: ${this.formatNumber(warehouse.inbound.packages + warehouse.outbound.packages)}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updateComparisonCharts(data) {
        this.createComparisonChart(data);
        this.createGrowthChart(data);
    }

    createComparisonChart(data) {
        const container = document.getElementById('comparisonChart');
        if (!container) return;

        // 销毁现有图表
        if (this.charts.comparisonChart) {
            this.charts.comparisonChart.dispose();
        }

        const chart = echarts.init(container);

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            legend: {
                data: ['当前期间', '上一期间'],
                bottom: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: ['进货票数', '进货板数', '进货件数', '出货票数', '出货板数', '出货件数']
            },
            yAxis: {
                type: 'value'
            },
            series: [
                {
                    name: '当前期间',
                    type: 'bar',
                    data: [
                        data.current.inbound.count,
                        data.current.inbound.pallets,
                        data.current.inbound.packages,
                        data.current.outbound.count,
                        data.current.outbound.pallets,
                        data.current.outbound.packages
                    ],
                    itemStyle: {
                        color: '#007bff'
                    }
                },
                {
                    name: '上一期间',
                    type: 'bar',
                    data: [
                        data.previous.inbound.count,
                        data.previous.inbound.pallets,
                        data.previous.inbound.packages,
                        data.previous.outbound.count,
                        data.previous.outbound.pallets,
                        data.previous.outbound.packages
                    ],
                    itemStyle: {
                        color: '#6c757d'
                    }
                }
            ]
        };

        chart.setOption(option);
        this.charts.comparisonChart = chart;

        // 响应式调整
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }

    createGrowthChart(data) {
        const container = document.getElementById('growthChart');
        if (!container) return;

        // 销毁现有图表
        if (this.charts.growthChart) {
            this.charts.growthChart.dispose();
        }

        const chart = echarts.init(container);

        // 准备增长率数据
        const growthData = [
            { name: '进货票数', value: data.growth.inbound.count },
            { name: '进货板数', value: data.growth.inbound.pallets },
            { name: '进货件数', value: data.growth.inbound.packages },
            { name: '出货票数', value: data.growth.outbound.count },
            { name: '出货板数', value: data.growth.outbound.pallets },
            { name: '出货件数', value: data.growth.outbound.packages }
        ];

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c}%'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                data: growthData.map(item => item.name)
            },
            series: [
                {
                    name: '增长率',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['60%', '50%'],
                    data: growthData.map(item => ({
                        name: item.name,
                        value: Math.abs(item.value),
                        itemStyle: {
                            color: item.value >= 0 ? '#28a745' : '#dc3545'
                        }
                    })),
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    label: {
                        formatter: function(params) {
                            const originalValue = growthData.find(item => item.name === params.name).value;
                            return `${params.name}\n${originalValue >= 0 ? '+' : ''}${originalValue.toFixed(1)}%`;
                        }
                    }
                }
            ]
        };

        chart.setOption(option);
        this.charts.growthChart = chart;

        // 响应式调整
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }

    formatNumber(num) {
        if (num === null || num === undefined) return '0';

        const number = parseFloat(num);
        if (isNaN(number)) return '0';

        if (number >= 1000000) {
            return (number / 1000000).toFixed(1) + 'M';
        } else if (number >= 1000) {
            return (number / 1000).toFixed(1) + 'K';
        } else {
            return number.toFixed(0);
        }
    }

    showError(message) {
        // 创建错误提示
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // 插入到页面顶部
        const container = document.querySelector('.container-fluid');
        container.insertAdjacentHTML('afterbegin', alertHtml);

        // 3秒后自动消失
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }

    updateWarehouseCards(data) {
        // 更新前端仓库卡片
        this.updateFrontendWarehouseCards(data);

        // 更新后端仓库卡片
        this.updateBackendWarehouseCards(data);

        // 更新汇总对比卡片
        this.updateSummaryComparisonCard(data);
    }

    updateFrontendWarehouseCards(data) {
        const warehouses = [
            { id: 1, name: '平湖仓', key: 'warehouse_1' },
            { id: 2, name: '昆山仓', key: 'warehouse_2' },
            { id: 3, name: '成都仓', key: 'warehouse_3' }
        ];

        warehouses.forEach(warehouse => {
            const warehouseData = data[warehouse.key] || {};
            const cardElement = document.getElementById(`warehouse-${warehouse.id}-data`);

            if (cardElement) {
                cardElement.innerHTML = this.generateWarehouseCardContent(warehouseData, warehouse.name);
            }
        });
    }

    updateBackendWarehouseCards(data) {
        const warehouseData = data.warehouse_4 || {};
        const cardElement = document.getElementById('warehouse-4-data');

        if (cardElement) {
            cardElement.innerHTML = this.generateWarehouseCardContent(warehouseData, '凭祥北投仓');
        }
    }

    updateSummaryComparisonCard(data) {
        const cardElement = document.getElementById('summary-comparison-data');

        if (cardElement) {
            cardElement.innerHTML = this.generateSummaryComparisonContent(data);
        }
    }

    generateWarehouseCardContent(data, warehouseName) {
        const today = data.today || { count: 0, pallets: 0, packages: 0, inbound: 0, outbound: 0 };
        const yesterday = data.yesterday || { count: 0, pallets: 0, packages: 0, inbound: 0, outbound: 0 };
        const lastYear = data.last_year || { count: 0, pallets: 0, packages: 0, inbound: 0, outbound: 0 };
        const inventory = data.inventory || { count: 0, pallets: 0, packages: 0 };

        // 计算同比增长率
        const yearOverYearGrowth = this.calculateGrowthRate(today.count, lastYear.count);
        const dayOverDayGrowth = this.calculateGrowthRate(today.count, yesterday.count);

        // 获取当前日期
        const currentDate = new Date();
        const todayDateStr = this.formatDateShort(currentDate);

        return `
            <div class="warehouse-stats">
                <!-- 今日进货数据 -->
                <div class="stat-section mb-3">
                    <h6 class="text-primary mb-2"><i class="fas fa-truck-loading me-1"></i> 今日进货 (${todayDateStr})</h6>
                    <div class="row g-2">
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-primary">${today.inbound || 0}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(today.pallets)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(today.packages)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 今日出货数据 -->
                <div class="stat-section mb-3">
                    <h6 class="text-success mb-2"><i class="fas fa-shipping-fast me-1"></i> 今日出货 (${todayDateStr})</h6>
                    <div class="row g-2">
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-success">${today.outbound || 0}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(today.outbound_pallets || 0)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(today.outbound_packages || 0)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 当前库存 -->
                <div class="stat-section mb-3">
                    <h6 class="text-warning mb-2"><i class="fas fa-boxes me-1"></i> 当前库存</h6>
                    <div class="row g-2">
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-warning">${inventory.count || 0}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.pallets || 0)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.packages || 0)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 超期库存 -->
                <div class="stat-section mb-3">
                    <h6 class="text-danger mb-2"><i class="fas fa-exclamation-triangle me-1"></i> 超期库存</h6>
                    <div class="row g-2 mb-2">
                        <div class="col-12">
                            <small class="text-muted">超出1天</small>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-danger">${inventory.overdue_1day?.count || 0}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.overdue_1day?.pallets || 0)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.overdue_1day?.packages || 0)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                    <div class="row g-2">
                        <div class="col-12">
                            <small class="text-muted">超出3天</small>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-danger">${inventory.overdue_3days?.count || 0}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.overdue_3days?.pallets || 0)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(inventory.overdue_3days?.packages || 0)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    generateSummaryComparisonContent(data) {
        const frontend = data.frontend_summary || { count: 0, pallets: 0, packages: 0 };
        const backend = data.backend_summary || { count: 0, pallets: 0, packages: 0 };
        const total = {
            count: frontend.count + backend.count,
            pallets: frontend.pallets + backend.pallets,
            packages: frontend.packages + backend.packages
        };

        return `
            <div class="summary-stats">
                <!-- 总计 -->
                <div class="stat-section mb-3">
                    <h6 class="text-primary mb-2"><i class="fas fa-chart-pie me-1"></i> 今日总计</h6>
                    <div class="row g-2">
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value text-primary">${total.count}</div>
                                <div class="stat-unit">票</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(total.pallets)}</div>
                                <div class="stat-unit">板</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-item text-center">
                                <div class="stat-value">${this.formatNumber(total.packages)}</div>
                                <div class="stat-unit">件</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 前后端对比 -->
                <div class="stat-section">
                    <h6 class="text-info mb-2"><i class="fas fa-balance-scale me-1"></i> 前后端对比</h6>
                    <div class="comparison-bars">
                        <div class="comparison-item mb-2">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="text-muted">前端仓</span>
                                <span class="fw-bold">${frontend.count}票</span>
                            </div>
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar bg-primary" style="width: ${total.count > 0 ? (frontend.count / total.count * 100) : 0}%"></div>
                            </div>
                        </div>
                        <div class="comparison-item">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="text-muted">后端仓</span>
                                <span class="fw-bold">${backend.count}票</span>
                            </div>
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar bg-warning" style="width: ${total.count > 0 ? (backend.count / total.count * 100) : 0}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    calculateGrowthRate(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous) * 100;
    }

    bindQueryEvents() {
        // 日对比查询
        const dayQueryBtn = document.getElementById('dayQueryBtn');
        if (dayQueryBtn) {
            dayQueryBtn.addEventListener('click', () => this.queryDayData());
        }

        // 周对比查询
        const weekQueryBtn = document.getElementById('weekQueryBtn');
        if (weekQueryBtn) {
            weekQueryBtn.addEventListener('click', () => this.queryWeekData());
        }

        // 月对比查询
        const monthQueryBtn = document.getElementById('monthQueryBtn');
        if (monthQueryBtn) {
            monthQueryBtn.addEventListener('click', () => this.queryMonthData());
        }

        // 年对比查询
        const yearQueryBtn = document.getElementById('yearQueryBtn');
        if (yearQueryBtn) {
            yearQueryBtn.addEventListener('click', () => this.queryYearData());
        }

        // 日期范围验证
        this.bindDateValidation();
    }

    bindDateValidation() {
        // 日期范围验证
        const dayStartDate = document.getElementById('dayStartDate');
        const dayEndDate = document.getElementById('dayEndDate');

        if (dayStartDate && dayEndDate) {
            const validateDayRange = () => {
                const start = new Date(dayStartDate.value);
                const end = new Date(dayEndDate.value);
                const diffDays = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

                if (diffDays > 7) {
                    alert('日期范围不能超过7天');
                    dayEndDate.value = dayStartDate.value;
                    const newEnd = new Date(start);
                    newEnd.setDate(newEnd.getDate() + 6);
                    dayEndDate.value = newEnd.toISOString().split('T')[0];
                }
            };

            dayStartDate.addEventListener('change', validateDayRange);
            dayEndDate.addEventListener('change', validateDayRange);
        }
    }

    async queryDayData() {
        const startDate = document.getElementById('dayStartDate').value;
        const endDate = document.getElementById('dayEndDate').value;

        if (!startDate || !endDate) {
            alert('请选择开始和结束日期');
            return;
        }

        try {
            const response = await fetch(`/reports/api/cargo_volume/day_range?start_date=${startDate}&end_date=${endDate}`);
            if (!response.ok) throw new Error('查询失败');

            const result = await response.json();
            if (!result.success) throw new Error(result.message);

            this.displayDayResults(result.data, startDate, endDate);
        } catch (error) {
            console.error('日对比查询失败:', error);
            alert('查询失败: ' + error.message);
        }
    }

    async queryWeekData() {
        const firstYear = document.getElementById('weekFirstYear').value;
        const firstMonth = document.getElementById('weekFirstMonth').value;
        const firstWeek = document.getElementById('weekFirstWeek').value;

        if (!firstYear || !firstMonth || !firstWeek) {
            alert('请选择第一周的年份、月份和周次');
            return;
        }

        // 获取第二周数据
        const secondYear = document.getElementById('weekSecondYear').value;
        const secondMonth = document.getElementById('weekSecondMonth').value;
        const secondWeek = document.getElementById('weekSecondWeek').value;

        if (!secondYear || !secondMonth || !secondWeek) {
            alert('请选择第二周的年份、月份和周次');
            return;
        }

        try {
            let url = `/reports/api/cargo_volume/week_range?first_year=${firstYear}&first_month=${firstMonth}&first_week=${firstWeek}&second_year=${secondYear}&second_month=${secondMonth}&second_week=${secondWeek}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error('查询失败');

            const result = await response.json();
            if (!result.success) throw new Error(result.message);

            this.displayWeekResults(result.data, firstYear, firstMonth, firstWeek, secondYear, secondMonth, secondWeek);
        } catch (error) {
            console.error('周对比查询失败:', error);
            alert('查询失败: ' + error.message);
        }
    }

    async queryMonthData() {
        if (!this.monthPickerState || !this.monthPickerState.startSelected || !this.monthPickerState.endSelected) {
            alert('请先选择完整的月份范围');
            return;
        }

        const startYear = this.monthPickerState.startYear;
        const startMonth = this.monthPickerState.startMonth;
        const endYear = this.monthPickerState.endYear;
        const endMonth = this.monthPickerState.endMonth;

        // 验证月份范围
        const start = new Date(startYear, startMonth - 1);
        const end = new Date(endYear, endMonth - 1);
        const monthDiff = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;

        if (start > end) {
            alert('起始月份不能晚于结束月份');
            return;
        }

        if (monthDiff > 12) {
            alert('月份范围不能超过12个月');
            return;
        }

        try {
            const response = await fetch(`/reports/api/cargo_volume/month_range?start_year=${startYear}&start_month=${startMonth}&end_year=${endYear}&end_month=${endMonth}`);
            if (!response.ok) throw new Error('查询失败');

            const result = await response.json();
            if (!result.success) throw new Error(result.message);

            this.displayMonthResults(result.data, startYear, startMonth, endYear, endMonth);
        } catch (error) {
            console.error('月对比查询失败:', error);
            alert('查询失败: ' + error.message);
        }
    }

    async queryYearData() {
        const startYear = document.getElementById('yearStartYear').value;
        const endYear = document.getElementById('yearEndYear').value;

        if (!startYear || !endYear) {
            alert('请选择开始和结束年份');
            return;
        }

        // 验证年份范围
        const yearDiff = parseInt(endYear) - parseInt(startYear) + 1;
        if (yearDiff > 5) {
            alert('年份范围不能超过5年');
            return;
        }

        if (parseInt(startYear) > parseInt(endYear)) {
            alert('开始年份不能晚于结束年份');
            return;
        }

        try {
            const response = await fetch(`/reports/api/cargo_volume/year_range?start_year=${startYear}&end_year=${endYear}`);
            if (!response.ok) throw new Error('查询失败');

            const result = await response.json();
            if (!result.success) throw new Error(result.message);

            this.displayYearResults(result.data, startYear, endYear);
        } catch (error) {
            console.error('年对比查询失败:', error);
            alert('查询失败: ' + error.message);
        }
    }

    displayDayResults(data, startDate, endDate) {
        const queryResultArea = document.getElementById('queryResultArea');
        const queryResultTitle = document.getElementById('queryResultTitle');
        const queryResultContent = document.getElementById('queryResultContent');

        queryResultTitle.innerHTML = `<i class="fas fa-calendar-day text-primary"></i> 日对比结果 (${startDate} 至 ${endDate})`;

        // 生成日对比结果HTML
        queryResultContent.innerHTML = this.generateDayResultsHTML(data);

        queryResultArea.style.display = 'block';
    }

    displayWeekResults(data, firstYear, firstMonth, firstWeek, secondYear, secondMonth, secondWeek) {
        const queryResultArea = document.getElementById('queryResultArea');
        const queryResultTitle = document.getElementById('queryResultTitle');
        const queryResultContent = document.getElementById('queryResultContent');

        let title = `<i class="fas fa-calendar-week text-primary"></i> 周对比结果 (${firstYear}年${firstMonth}月第${firstWeek}周`;
        if (secondYear && secondMonth && secondWeek) {
            title += ` vs ${secondYear}年${secondMonth}月第${secondWeek}周`;
        }
        title += ')';

        queryResultTitle.innerHTML = title;
        queryResultContent.innerHTML = this.generateWeekResultsHTML(data);

        queryResultArea.style.display = 'block';
    }

    displayMonthResults(data, startYear, startMonth, endYear, endMonth) {
        const queryResultArea = document.getElementById('queryResultArea');
        const queryResultTitle = document.getElementById('queryResultTitle');
        const queryResultContent = document.getElementById('queryResultContent');

        queryResultTitle.innerHTML = `<i class="fas fa-calendar-alt text-primary"></i> 月对比结果 (${startYear}年${startMonth}月 至 ${endYear}年${endMonth}月)`;
        queryResultContent.innerHTML = this.generateMonthResultsHTML(data);

        queryResultArea.style.display = 'block';
    }

    displayYearResults(data, startYear, endYear) {
        const queryResultArea = document.getElementById('queryResultArea');
        const queryResultTitle = document.getElementById('queryResultTitle');
        const queryResultContent = document.getElementById('queryResultContent');

        queryResultTitle.innerHTML = `<i class="fas fa-calendar text-primary"></i> 年对比结果 (${startYear}年 至 ${endYear}年)`;
        queryResultContent.innerHTML = this.generateYearResultsHTML(data);

        queryResultArea.style.display = 'block';
    }

    generateDayResultsHTML(data) {
        // 这里将生成日对比结果的HTML
        return `
            <div class="query-result-summary">
                <div class="row">
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.summary?.total_count || 0}</div>
                            <div class="summary-label">总票数</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_pallets || 0)}</div>
                            <div class="summary-label">总托盘</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_packages || 0)}</div>
                            <div class="summary-label">总包裹</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.daily_data?.length || 0}</div>
                            <div class="summary-label">查询天数</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="table-responsive warehouse-table-container">
                <table class="table table-striped query-result-table warehouse-grouped-table">
                    <thead>
                        <tr>
                            <th rowspan="2" class="align-middle date-column">日期</th>
                            <th colspan="3" class="text-center warehouse-header-ph warehouse-icon" title="平湖仓数据">平湖仓</th>
                            <th colspan="3" class="text-center warehouse-header-ks warehouse-icon" title="昆山仓数据">昆山仓</th>
                            <th colspan="3" class="text-center warehouse-header-cd warehouse-icon" title="成都仓数据">成都仓</th>
                            <th colspan="3" class="text-center warehouse-header-px warehouse-icon" title="凭祥北投仓数据">凭祥北投仓</th>
                            <th colspan="3" class="text-center warehouse-header-total total-icon" title="汇总数据">合计</th>
                        </tr>
                        <tr>
                            <th class="text-center small warehouse-group-ph group-start">票数</th>
                            <th class="text-center small warehouse-group-ph">板数</th>
                            <th class="text-center small warehouse-group-ph group-end">件数</th>
                            <th class="text-center small warehouse-group-ks group-start">票数</th>
                            <th class="text-center small warehouse-group-ks">板数</th>
                            <th class="text-center small warehouse-group-ks group-end">件数</th>
                            <th class="text-center small warehouse-group-cd group-start">票数</th>
                            <th class="text-center small warehouse-group-cd">板数</th>
                            <th class="text-center small warehouse-group-cd group-end">件数</th>
                            <th class="text-center small warehouse-group-px group-start">票数</th>
                            <th class="text-center small warehouse-group-px">板数</th>
                            <th class="text-center small warehouse-group-px group-end">件数</th>
                            <th class="text-center small warehouse-group-total group-start">票数</th>
                            <th class="text-center small warehouse-group-total">板数</th>
                            <th class="text-center small warehouse-group-total group-end">件数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(data.daily_data || []).map(day => `
                            <tr>
                                <td class="date-column"><strong>${day.date}</strong></td>
                                <td class="text-center warehouse-group-ph group-start">${day.warehouse_1 || 0}</td>
                                <td class="text-center warehouse-group-ph">${this.formatNumber(day.warehouse_1_pallets || 0)}</td>
                                <td class="text-center warehouse-group-ph group-end">${this.formatNumber(day.warehouse_1_packages || 0)}</td>
                                <td class="text-center warehouse-group-ks group-start">${day.warehouse_2 || 0}</td>
                                <td class="text-center warehouse-group-ks">${this.formatNumber(day.warehouse_2_pallets || 0)}</td>
                                <td class="text-center warehouse-group-ks group-end">${this.formatNumber(day.warehouse_2_packages || 0)}</td>
                                <td class="text-center warehouse-group-cd group-start">${day.warehouse_3 || 0}</td>
                                <td class="text-center warehouse-group-cd">${this.formatNumber(day.warehouse_3_pallets || 0)}</td>
                                <td class="text-center warehouse-group-cd group-end">${this.formatNumber(day.warehouse_3_packages || 0)}</td>
                                <td class="text-center warehouse-group-px group-start">${day.warehouse_4 || 0}</td>
                                <td class="text-center warehouse-group-px">${this.formatNumber(day.warehouse_4_pallets || 0)}</td>
                                <td class="text-center warehouse-group-px group-end">${this.formatNumber(day.warehouse_4_packages || 0)}</td>
                                <td class="text-center warehouse-group-total group-start"><strong>${day.total || 0}</strong></td>
                                <td class="text-center warehouse-group-total"><strong>${this.formatNumber(day.total_pallets || 0)}</strong></td>
                                <td class="text-center warehouse-group-total group-end"><strong>${this.formatNumber(day.total_packages || 0)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    generateWeekResultsHTML(data) {
        // 生成周对比结果HTML
        const hasSecondWeek = data.second_week ? true : false;

        let html = `
            <div class="query-result-summary">
                <div class="row">
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.summary?.total_count || 0}</div>
                            <div class="summary-label">总票数</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_pallets || 0)}</div>
                            <div class="summary-label">总托盘</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_packages || 0)}</div>
                            <div class="summary-label">总包裹</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${hasSecondWeek ? '2' : '1'}</div>
                            <div class="summary-label">对比周数</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (hasSecondWeek) {
            // 双周对比表格 - 只显示周汇总
            html += `
                <div class="table-responsive warehouse-table-container">
                    <table class="table table-striped query-result-table warehouse-grouped-table">
                        <thead>
                            <tr>
                                <th rowspan="2" class="align-middle">周次</th>
                                <th colspan="3" class="text-center warehouse-header-ph warehouse-icon" title="平湖仓数据">平湖仓</th>
                                <th colspan="3" class="text-center warehouse-header-ks warehouse-icon" title="昆山仓数据">昆山仓</th>
                                <th colspan="3" class="text-center warehouse-header-cd warehouse-icon" title="成都仓数据">成都仓</th>
                                <th colspan="3" class="text-center warehouse-header-px warehouse-icon" title="凭祥北投仓数据">凭祥北投仓</th>
                                <th colspan="3" class="text-center warehouse-header-total total-icon" title="汇总数据">合计</th>
                            </tr>
                            <tr>
                                <th class="text-center small warehouse-group-ph group-start">票数</th>
                                <th class="text-center small warehouse-group-ph">板数</th>
                                <th class="text-center small warehouse-group-ph group-end">件数</th>
                                <th class="text-center small warehouse-group-ks group-start">票数</th>
                                <th class="text-center small warehouse-group-ks">板数</th>
                                <th class="text-center small warehouse-group-ks group-end">件数</th>
                                <th class="text-center small warehouse-group-cd group-start">票数</th>
                                <th class="text-center small warehouse-group-cd">板数</th>
                                <th class="text-center small warehouse-group-cd group-end">件数</th>
                                <th class="text-center small">票数</th>
                                <th class="text-center small">板数</th>
                                <th class="text-center small">件数</th>
                                <th class="text-center small">票数</th>
                                <th class="text-center small">板数</th>
                                <th class="text-center small">件数</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>${data.first_week.name}<br><small class="text-muted">(${data.first_week.date_range.start} 至 ${data.first_week.date_range.end})</small></strong></td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4_packages'))}</td>
                                <td class="text-center"><strong>${data.first_week.summary.total_count}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.first_week.summary.total_pallets)}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.first_week.summary.total_packages)}</strong></td>
                            </tr>
                            <tr>
                                <td><strong>${data.second_week.name}<br><small class="text-muted">(${data.second_week.date_range.start} 至 ${data.second_week.date_range.end})</small></strong></td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_1')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_1_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_1_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_2')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_2_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_2_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_3')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_3_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_3_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_4')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_4_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.second_week.daily_data, 'warehouse_4_packages'))}</td>
                                <td class="text-center"><strong>${data.second_week.summary.total_count}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.second_week.summary.total_pallets)}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.second_week.summary.total_packages)}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            // 单周表格 - 只显示周汇总
            html += `
                <div class="table-responsive warehouse-table-container">
                    <table class="table table-striped query-result-table warehouse-grouped-table">
                        <thead>
                            <tr>
                                <th rowspan="2" class="align-middle">周次</th>
                                <th colspan="3" class="text-center warehouse-header-ph warehouse-icon" title="平湖仓数据">平湖仓</th>
                                <th colspan="3" class="text-center warehouse-header-ks warehouse-icon" title="昆山仓数据">昆山仓</th>
                                <th colspan="3" class="text-center warehouse-header-cd warehouse-icon" title="成都仓数据">成都仓</th>
                                <th colspan="3" class="text-center warehouse-header-px warehouse-icon" title="凭祥北投仓数据">凭祥北投仓</th>
                                <th colspan="3" class="text-center warehouse-header-total total-icon" title="汇总数据">合计</th>
                            </tr>
                            <tr>
                                <th class="text-center small warehouse-group-ph group-start">票数</th>
                                <th class="text-center small warehouse-group-ph">板数</th>
                                <th class="text-center small warehouse-group-ph group-end">件数</th>
                                <th class="text-center small warehouse-group-ks group-start">票数</th>
                                <th class="text-center small warehouse-group-ks">板数</th>
                                <th class="text-center small warehouse-group-ks group-end">件数</th>
                                <th class="text-center small warehouse-group-cd group-start">票数</th>
                                <th class="text-center small warehouse-group-cd">板数</th>
                                <th class="text-center small warehouse-group-cd group-end">件数</th>
                                <th class="text-center small">票数</th>
                                <th class="text-center small">板数</th>
                                <th class="text-center small">件数</th>
                                <th class="text-center small">票数</th>
                                <th class="text-center small">板数</th>
                                <th class="text-center small">件数</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>${data.first_week.name}<br><small class="text-muted">(${data.first_week.date_range.start} 至 ${data.first_week.date_range.end})</small></strong></td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_1_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_2_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_3_packages'))}</td>
                                <td class="text-center">${this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4')}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4_pallets'))}</td>
                                <td class="text-center">${this.formatNumber(this.calculateWeekWarehouseTotal(data.first_week.daily_data, 'warehouse_4_packages'))}</td>
                                <td class="text-center"><strong>${data.first_week.summary.total_count}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.first_week.summary.total_pallets)}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(data.first_week.summary.total_packages)}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `;
        }

        return html;
    }

    calculateWeekWarehouseTotal(dailyData, warehouseKey) {
        return (dailyData || []).reduce((total, day) => total + (day[warehouseKey] || 0), 0);
    }

    generateMonthResultsHTML(data) {
        // 生成月对比结果HTML
        return `
            <div class="query-result-summary">
                <div class="row">
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.summary?.total_count || 0}</div>
                            <div class="summary-label">总票数</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_pallets || 0)}</div>
                            <div class="summary-label">总托盘</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_packages || 0)}</div>
                            <div class="summary-label">总包裹</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.month_data?.length || 0}</div>
                            <div class="summary-label">查询月数</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped query-result-table">
                    <thead>
                        <tr>
                            <th rowspan="2" class="align-middle">月份</th>
                            <th colspan="3" class="text-center">平湖仓</th>
                            <th colspan="3" class="text-center">昆山仓</th>
                            <th colspan="3" class="text-center">成都仓</th>
                            <th colspan="3" class="text-center">凭祥北投仓</th>
                            <th colspan="3" class="text-center">合计</th>
                        </tr>
                        <tr>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(data.month_data || []).map(month => `
                            <tr>
                                <td><strong>${month.month_name}</strong></td>
                                <td class="text-center">${month.warehouse_1 || 0}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_1_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_1_packages || 0)}</td>
                                <td class="text-center">${month.warehouse_2 || 0}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_2_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_2_packages || 0)}</td>
                                <td class="text-center">${month.warehouse_3 || 0}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_3_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_3_packages || 0)}</td>
                                <td class="text-center">${month.warehouse_4 || 0}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_4_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(month.warehouse_4_packages || 0)}</td>
                                <td class="text-center"><strong>${month.total || 0}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(month.total_pallets || 0)}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(month.total_packages || 0)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    generateYearResultsHTML(data) {
        // 生成年对比结果HTML
        return `
            <div class="query-result-summary">
                <div class="row">
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.summary?.total_count || 0}</div>
                            <div class="summary-label">总票数</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_pallets || 0)}</div>
                            <div class="summary-label">总托盘</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${this.formatNumber(data.summary?.total_packages || 0)}</div>
                            <div class="summary-label">总包裹</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="summary-item">
                            <div class="summary-value">${data.year_data?.length || 0}</div>
                            <div class="summary-label">查询年数</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped query-result-table">
                    <thead>
                        <tr>
                            <th rowspan="2" class="align-middle">年份</th>
                            <th colspan="3" class="text-center">平湖仓</th>
                            <th colspan="3" class="text-center">昆山仓</th>
                            <th colspan="3" class="text-center">成都仓</th>
                            <th colspan="3" class="text-center">凭祥北投仓</th>
                            <th colspan="3" class="text-center">合计</th>
                        </tr>
                        <tr>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                            <th class="text-center small">票数</th>
                            <th class="text-center small">板数</th>
                            <th class="text-center small">件数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(data.year_data || []).map(year => `
                            <tr>
                                <td><strong>${year.year_name}</strong></td>
                                <td class="text-center">${year.warehouse_1 || 0}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_1_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_1_packages || 0)}</td>
                                <td class="text-center">${year.warehouse_2 || 0}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_2_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_2_packages || 0)}</td>
                                <td class="text-center">${year.warehouse_3 || 0}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_3_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_3_packages || 0)}</td>
                                <td class="text-center">${year.warehouse_4 || 0}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_4_pallets || 0)}</td>
                                <td class="text-center">${this.formatNumber(year.warehouse_4_packages || 0)}</td>
                                <td class="text-center"><strong>${year.total || 0}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(year.total_pallets || 0)}</strong></td>
                                <td class="text-center"><strong>${this.formatNumber(year.total_packages || 0)}</strong></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
}

// 应用仓库卡片自定义样式
function applyWarehouseCardStyles() {
    console.log('🎨 开始应用仓库卡片自定义样式...');

    // 定义每个仓库卡片的颜色方案
    const cardStyles = {
        'pinghu-card': {
            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
            borderColor: '#2196f3',
            shadowColor: 'rgba(33, 150, 243, 0.3)'
        },
        'kunshan-card': {
            background: 'linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%)',
            borderColor: '#4caf50',
            shadowColor: 'rgba(76, 175, 80, 0.3)'
        },
        'chengdu-card': {
            background: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)',
            borderColor: '#ff9800',
            shadowColor: 'rgba(255, 152, 0, 0.3)'
        },
        'pingxiang-card': {
            background: 'linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%)',
            borderColor: '#e91e63',
            shadowColor: 'rgba(233, 30, 99, 0.3)'
        }
    };

    // 应用样式到每个卡片
    Object.keys(cardStyles).forEach(cardClass => {
        const cards = document.querySelectorAll(`.${cardClass}`);
        const style = cardStyles[cardClass];

        console.log(`🎯 应用样式到 ${cardClass}，找到 ${cards.length} 个卡片`);

        cards.forEach((card, index) => {
            console.log(`- 处理卡片 ${index + 1}:`, card);

            // 应用背景渐变 (使用 setProperty 和 important)
            card.style.setProperty('background', style.background, 'important');
            card.style.setProperty('background-image', style.background, 'important');
            card.style.setProperty('border-color', style.borderColor, 'important');
            card.style.setProperty('border', `2px solid ${style.borderColor}`, 'important');
            card.style.setProperty('box-shadow', `0 10px 30px ${style.shadowColor}`, 'important');
            card.style.setProperty('transition', 'all 0.3s ease', 'important');

            // 强制移除可能冲突的类
            card.classList.remove('bg-primary', 'bg-secondary', 'bg-success', 'bg-info', 'bg-warning', 'bg-danger');

            // 移除原有的悬停事件监听器（避免重复绑定）
            card.removeEventListener('mouseenter', card._hoverEnter);
            card.removeEventListener('mouseleave', card._hoverLeave);

            // 创建新的悬停效果函数
            card._hoverEnter = function() {
                this.style.setProperty('box-shadow', `0 25px 50px ${style.shadowColor}`, 'important');
                this.style.setProperty('transform', 'translateY(-8px)', 'important');
            };

            card._hoverLeave = function() {
                this.style.setProperty('box-shadow', `0 10px 30px ${style.shadowColor}`, 'important');
                this.style.setProperty('transform', 'translateY(0)', 'important');
            };

            // 绑定悬停效果
            card.addEventListener('mouseenter', card._hoverEnter);
            card.addEventListener('mouseleave', card._hoverLeave);

            console.log(`✅ 卡片 ${cardClass} 样式已应用 (使用 !important)`);
        });
    });

    console.log('🎨 仓库卡片样式应用完成！');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new CargoVolumeDashboard();

    // 延迟应用样式，确保数据加载完成
    setTimeout(function() {
        console.log('🚀 开始应用仓库卡片样式...');
        applyWarehouseCardStyles();

        // 监听数据更新，重新应用样式
        const observer = new MutationObserver(function(mutations) {
            let shouldReapplyStyles = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' &&
                    mutation.target.id &&
                    mutation.target.id.includes('warehouse-') &&
                    mutation.target.id.includes('-data')) {
                    shouldReapplyStyles = true;
                }
            });

            if (shouldReapplyStyles) {
                console.log('🔄 检测到仓库数据更新，重新应用样式...');
                setTimeout(applyWarehouseCardStyles, 100);
            }
        });

        // 监听仓库卡片数据区域的变化
        const warehouseDataElements = document.querySelectorAll('[id^="warehouse-"][id$="-data"]');
        warehouseDataElements.forEach(element => {
            observer.observe(element, { childList: true, subtree: true });
        });

    }, 1000); // 延迟1秒确保数据加载完成
});
