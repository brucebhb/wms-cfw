/**
 * 基于flatpickr的日期时间选择器实现
 */

// 立即执行函数，避免变量污染全局作用域
(function() {
  console.log('flatpickr日期时间选择器初始化开始...');
  
  // 确保在DOM加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // 如果DOM已经加载完成，立即初始化
    init();
  }
  
  function init() {
    console.log('DOM已加载，开始初始化flatpickr...');
    
    // 检查flatpickr是否已加载
    if (typeof flatpickr === 'undefined') {
      console.log('flatpickr未加载，正在动态加载...');
      loadFlatpickr(initDateTimePickers);
    } else {
      console.log('flatpickr已加载，直接初始化选择器');
      initDateTimePickers();
    }
  }
  
  // 动态加载flatpickr及其语言包
  function loadFlatpickr(callback) {
    // 加载CSS
    const linkElem = document.createElement('link');
    linkElem.rel = 'stylesheet';
    linkElem.href = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css';
    document.head.appendChild(linkElem);
    
    // 加载主文件
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/flatpickr';
    script.onload = function() {
      console.log('flatpickr主文件加载完成');
      // 加载中文语言包
      const langScript = document.createElement('script');
      langScript.src = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/l10n/zh.js';
      langScript.onload = function() {
        console.log('flatpickr中文语言包加载完成');
        if (callback && typeof callback === 'function') {
          callback();
        }
      };
      langScript.onerror = function(error) {
        console.error('加载中文语言包失败:', error);
        // 即使语言包加载失败，也尝试初始化
        if (callback && typeof callback === 'function') {
          callback();
        }
      };
      document.head.appendChild(langScript);
    };
    script.onerror = function(error) {
      console.error('加载flatpickr主文件失败:', error);
      // 显示错误消息
      showErrorMessage('日期选择器加载失败，请刷新页面重试');
    };
    document.head.appendChild(script);
  }
  
  // 初始化所有日期时间输入框
  function initDateTimePickers() {
    console.log('开始初始化日期时间选择器...');
    
    // 查找所有带有data-flatpickr属性的元素
    const flatpickrGroups = document.querySelectorAll('[data-flatpickr]');
    console.log(`找到 ${flatpickrGroups.length} 个日期时间选择器组`);
    
    if (flatpickrGroups.length === 0) {
      console.log('未找到日期时间选择器组，尝试其他选择器');
      
      // 尝试按旧方式查找
      const dateTimeInputs = document.querySelectorAll('[data-datetime]');
      if (dateTimeInputs.length > 0) {
        console.log(`找到 ${dateTimeInputs.length} 个日期时间输入框，尝试初始化`);
        initLegacyInputs(dateTimeInputs);
        return;
      }
      
      // 最后尝试查找所有时间相关的输入框
      const timeInputs = document.querySelectorAll('input[id*="time"]');
      if (timeInputs.length > 0) {
        console.log(`找到 ${timeInputs.length} 个可能的时间输入框，尝试初始化`);
        initLegacyInputs(timeInputs);
      }
    } else {
      // 初始化所有找到的flatpickr组
      flatpickrGroups.forEach(initFlatpickrGroup);
    }
    
    // 创建调试按钮
    createDebugButton();
  }
  
  // 初始化单个flatpickr组
  function initFlatpickrGroup(group) {
    try {
      // 从属性中读取配置
      const inputId = group.getAttribute('data-input-id');
      const enableTime = group.getAttribute('data-enable-time') === 'true';
      const noCalendar = group.getAttribute('data-no-calendar') === 'true';
      const dateFormat = group.getAttribute('data-date-format') || 'Y-m-d H:i';
      
      console.log(`初始化flatpickr组: ${inputId}`, {
        enableTime,
        noCalendar,
        dateFormat
      });
      
      // 配置选项
      const options = {
        enableTime: enableTime,
        noCalendar: noCalendar,
        dateFormat: dateFormat,
        locale: 'zh',
        time_24hr: true,
        allowInput: true,
        disableMobile: false,
        clickOpens: true
      };
      
      // 获取组内的输入元素和触发器
      const input = group.querySelector('input');
      const trigger = group.querySelector('.flatpickr-trigger');
      
      if (!input) {
        console.error(`未找到${inputId}的输入元素`);
        return;
      }
      
      // 初始化flatpickr
      const fp = flatpickr(input, options);
      console.log(`${inputId || '未命名输入框'}初始化完成`);
      
      // 保存实例到元素
      input._flatpickr = fp;
      
      // 绑定触发器点击事件
      if (trigger) {
        trigger.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          if (input._flatpickr) {
            input._flatpickr.open();
          }
          return false;
        });
      }
      
      // 为输入框添加点击事件
      input.addEventListener('click', function(e) {
        if (this._flatpickr) {
          this._flatpickr.open();
        }
      });
      
      // 确保失去焦点时更新值
      input.addEventListener('blur', function() {
        if (this._flatpickr) {
          this._flatpickr.formatDate(this._flatpickr.selectedDates[0], dateFormat);
        }
      });
      
    } catch (error) {
      console.error('初始化flatpickr组时出错:', error);
    }
  }
  
  // 旧方式初始化输入框
  function initLegacyInputs(inputs) {
    inputs.forEach(function(input) {
      try {
        const id = input.id || '未命名输入框';
        console.log(`使用传统方式初始化: ${id}`);
        
        // 检查是否是日期或时间专用
        const isDateOnly = input.hasAttribute('data-date-only');
        const isTimeOnly = input.hasAttribute('data-time-only');
        
        // 配置选项
        const options = {
          enableTime: !isDateOnly,
          noCalendar: isTimeOnly,
          dateFormat: isDateOnly ? 'Y-m-d' : (isTimeOnly ? 'H:i' : 'Y-m-d H:i'),
          locale: 'zh',
          time_24hr: true,
          allowInput: true,
          disableMobile: false,
          clickOpens: true
        };
        
        // 初始化flatpickr
        const fp = flatpickr(input, options);
        input._flatpickr = fp;
        console.log(`${id} 初始化成功`);
        
        // 尝试查找相关的图标触发器
        const parent = input.parentElement;
        if (parent) {
          const icon = parent.querySelector('.input-group-text, [class*="calendar"], [class*="clock"]');
          if (icon) {
            icon.addEventListener('click', function() {
              if (input._flatpickr) {
                input._flatpickr.open();
              }
            });
          }
        }
      } catch (err) {
        console.error('初始化输入框失败:', err);
      }
    });
  }
  
  // 创建调试按钮
  function createDebugButton() {
    const existingBtn = document.getElementById('flatpickr-debug-btn');
    if (existingBtn) {
      existingBtn.remove();
    }
    
    const btn = document.createElement('button');
    btn.id = 'flatpickr-debug-btn';
    btn.textContent = '初始化日期选择器';
    btn.className = 'btn btn-sm btn-info position-fixed';
    btn.style.bottom = '10px';
    btn.style.right = '10px';
    btn.style.zIndex = '9999';
    
    btn.addEventListener('click', function() {
      console.log('手动重新初始化日期选择器');
      initDateTimePickers();
    });
    
    document.body.appendChild(btn);
  }
  
  // 显示错误消息
  function showErrorMessage(message) {
    // 如果页面上已有sweetalert2库
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: '错误',
        text: message,
        icon: 'error',
        confirmButtonText: '确定'
      });
    } else {
      // 使用简单的alert
      alert(message);
    }
  }
})();

// 帮助函数：向表单中添加日期时间选择器
function createDateTimePicker(containerId, inputId, label, required = false, isDateOnly = false, isTimeOnly = false) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // 创建标签元素
  const labelElem = document.createElement('label');
  labelElem.htmlFor = inputId;
  labelElem.textContent = label;
  if (required) {
    labelElem.classList.add('required-field');
  }
  
  // 创建输入框组
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group flatpickr-input-group';
  inputGroup.setAttribute('data-flatpickr', '');
  inputGroup.setAttribute('data-input-id', inputId);
  inputGroup.setAttribute('data-enable-time', isDateOnly ? 'false' : 'true');
  inputGroup.setAttribute('data-no-calendar', isTimeOnly ? 'true' : 'false');
  inputGroup.setAttribute('data-date-format', 
      isDateOnly ? 'Y-m-d' : (isTimeOnly ? 'H:i' : 'Y-m-d H:i'));
  
  // 创建输入框
  const input = document.createElement('input');
  input.type = 'text';
  input.id = inputId;
  input.name = inputId;
  input.className = 'form-control flatpickr-input';
  input.dataset.datetime = 'true';
  
  // 设置日期或时间选项
  if (isDateOnly) {
    input.dataset.dateOnly = 'true';
    input.placeholder = 'YYYY-MM-DD';
  } else if (isTimeOnly) {
    input.dataset.timeOnly = 'true';
    input.placeholder = 'HH:MM';
  } else {
    input.placeholder = 'YYYY-MM-DD HH:MM';
  }
  
  if (required) {
    input.required = true;
  }
  
  // 创建触发器
  const trigger = document.createElement('span');
  trigger.className = 'input-group-text cursor-pointer flatpickr-trigger';
  
  const icon = document.createElement('i');
  icon.className = isTimeOnly ? 'fas fa-clock' : 'fas fa-calendar-alt';
  trigger.appendChild(icon);
  
  // 组装输入组
  inputGroup.appendChild(input);
  inputGroup.appendChild(trigger);
  
  // 创建包装元素
  const wrapper = document.createElement('div');
  wrapper.className = 'date-time-container flatpickr-wrapper';
  wrapper.id = `${inputId}-container`;
  wrapper.appendChild(labelElem);
  wrapper.appendChild(inputGroup);
  
  // 添加到容器
  container.appendChild(wrapper);
  
  return input;
} 