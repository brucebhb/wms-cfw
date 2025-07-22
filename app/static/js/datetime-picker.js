// 日期时间选择器组件
// 将日期选择和时间输入分开处理，提高性能和用户体验

$(document).ready(function() {
  console.log('日期时间选择器初始化开始...');
  
  // 确保DateRangePicker库已加载
  if (typeof $.fn.daterangepicker === 'undefined') {
    console.error('错误: daterangepicker库未加载！');
    
    // 尝试动态加载daterangepicker
    loadDaterangepicker(function() {
      // 库加载成功后初始化选择器
      initDateTimePickers();
    });
  } else {
    console.log('daterangepicker库已加载，开始初始化选择器');
    // 初始化所有日期时间选择器
    initDateTimePickers();
  }
  
  // 动态加载daterangepicker库
  function loadDaterangepicker(callback) {
    console.log('正在动态加载daterangepicker库...');
    
    // 检查moment是否已加载
    if (typeof moment === 'undefined') {
      console.log('正在加载moment.js...');
      const momentScript = document.createElement('script');
      momentScript.src = 'https://cdn.jsdelivr.net/npm/moment/moment.min.js';
      momentScript.onload = function() {
        console.log('moment.js加载完成，正在加载daterangepicker...');
        loadDaterangepickerScript(callback);
      };
      momentScript.onerror = function() {
        console.error('加载moment.js失败!');
      };
      document.head.appendChild(momentScript);
    } else {
      loadDaterangepickerScript(callback);
    }
    
    function loadDaterangepickerScript(callback) {
      // 加载CSS
      if (!document.querySelector('link[href*="daterangepicker.css"]')) {
        const linkElem = document.createElement('link');
        linkElem.rel = 'stylesheet';
        linkElem.href = 'https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.css';
        document.head.appendChild(linkElem);
      }
      
      // 加载JS
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.min.js';
      script.onload = function() {
        console.log('daterangepicker.js加载完成!');
        callback();
      };
      script.onerror = function() {
        console.error('加载daterangepicker.js失败!');
      };
      document.head.appendChild(script);
    }
  }
  
  function initDateTimePickers() {
    console.log('开始初始化日期时间选择器...');
    const containers = $('.date-time-picker-container');
    console.log(`找到 ${containers.length} 个日期时间选择器容器`);
    
    containers.each(function() {
      var $container = $(this);
      var $dateInput = $container.find('.date-input');
      var $timeInput = $container.find('.time-input');
      var $hiddenInput = $container.find('.datetime-value');
      var $calendarBtn = $container.find('.calendar-btn');
      
      console.log('初始化日期选择器:', $dateInput.attr('id'));

      try {
        // 初始化日期选择器
        $dateInput.daterangepicker({
          singleDatePicker: true,
          showDropdowns: true,
          autoApply: true,
          opens: 'center',
          locale: {
            format: 'YYYY-MM-DD',
            daysOfWeek: ['日', '一', '二', '三', '四', '五', '六'],
            monthNames: ['一月', '二月', '三月', '四月', '五月', '六月', 
                        '七月', '八月', '九月', '十月', '十一月', '十二月'],
            firstDay: 1
          },
          autoUpdateInput: true
        });
        
        console.log('日期选择器初始化成功:', $dateInput.attr('id'));
      } catch (e) {
        console.error('初始化日期选择器出错:', e);
      }

      // 日期选择后更新隐藏字段
      $dateInput.on('apply.daterangepicker', function(ev, picker) {
        console.log('日期已选择:', picker.startDate.format('YYYY-MM-DD'));
        updateHiddenField($container);
      });

      // 时间输入格式控制和验证
      $timeInput.on('input', function() {
        var value = $(this).val();
        
        // 只允许输入数字和冒号
        value = value.replace(/[^\d:]/g, '');
        
        // 自动添加冒号
        if (value.length === 2 && !value.includes(':')) {
          value += ':';
        }
        
        $(this).val(value);
        updateHiddenField($container);
      });

      // 时间输入失去焦点时验证格式
      $timeInput.on('blur', function() {
        var value = $(this).val();
        
        // 如果是空值，设置默认值00:00
        if (!value) {
          $(this).val('00:00');
        } else {
          // 验证并修正时间格式
          var parts = value.split(':');
          var hours = parts[0] ? parseInt(parts[0]) : 0;
          var minutes = parts.length > 1 ? parseInt(parts[1]) : 0;
          
          if (hours > 23) hours = 23;
          if (minutes > 59) minutes = 59;
          
          $(this).val(String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0'));
        }
        
        updateHiddenField($container);
      });

      // 点击日历按钮时打开日期选择器
      $calendarBtn.on('click', function() {
        console.log('日历按钮被点击');
        $dateInput.focus();
        try {
          // 尝试手动打开日历
          $dateInput.data('daterangepicker').show();
        } catch (e) {
          console.error('手动打开日历时出错:', e);
        }
      });

      // 如果已有初始值，则进行设置
      if ($hiddenInput.val()) {
        setInitialValues($container);
      } else {
        // 设置默认值为今天
        var today = new Date();
        $dateInput.val(formatDate(today));
        $timeInput.val('00:00');
        updateHiddenField($container);
      }
    });
    
    // 添加全局点击处理器来检查日期选择器点击问题
    $(document).on('click', '.date-input, .calendar-btn', function(e) {
      console.log('日期输入框或日历按钮被点击:', e.target);
    });
  }

  // 更新隐藏字段中的完整日期时间值
  function updateHiddenField($container) {
    var $dateInput = $container.find('.date-input');
    var $timeInput = $container.find('.time-input');
    var $hiddenInput = $container.find('.datetime-value');
    
    var dateValue = $dateInput.val();
    var timeValue = $timeInput.val() || '00:00';
    
    if (dateValue) {
      $hiddenInput.val(dateValue + ' ' + timeValue);
    } else {
      $hiddenInput.val('');
    }
    
    // 触发change事件，以便其他依赖此值的代码可以响应
    $hiddenInput.trigger('change');
    console.log('隐藏字段已更新:', $hiddenInput.val());
  }
  
  // 从隐藏字段设置初始值
  function setInitialValues($container) {
    var $dateInput = $container.find('.date-input');
    var $timeInput = $container.find('.time-input');
    var $hiddenInput = $container.find('.datetime-value');
    
    var fullValue = $hiddenInput.val();
    if (fullValue) {
      try {
        // 尝试解析日期时间字符串
        var date = new Date(fullValue);
        if (!isNaN(date.getTime())) {
          // 设置日期部分 (YYYY-MM-DD)
          $dateInput.val(formatDate(date));
          
          // 设置时间部分 (HH:MM)
          var hours = String(date.getHours()).padStart(2, '0');
          var minutes = String(date.getMinutes()).padStart(2, '0');
          $timeInput.val(`${hours}:${minutes}`);
        }
      } catch (e) {
        console.error('解析日期时间出错:', e);
      }
    }
  }
  
  // 格式化日期为YYYY-MM-DD
  function formatDate(date) {
    var year = date.getFullYear();
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}); 