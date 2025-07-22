/**
 * 带冒号的时间输入处理脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('带冒号的时间输入处理脚本已加载');
  
  // 设置当前日期为默认值
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(function(input) {
    if (!input.value) {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      
      const defaultValue = `${year}-${month}-${day}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名日期输入框'} 设置默认值: ${defaultValue}`);
    }
  });
  
  // 处理时间输入框
  const timeInputs = document.querySelectorAll('.time-with-colon');
  timeInputs.forEach(function(input) {
    // 设置当前时间为默认值
    if (!input.value) {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      
      const defaultValue = `${hours}:${minutes}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名时间输入框'} 设置默认值: ${defaultValue}`);
    }
    
    // 监听输入事件
    input.addEventListener('input', function(e) {
      formatTimeWithColon(this);
      validateTimeFormat(this);
    });
    
    // 失去焦点时格式化
    input.addEventListener('blur', function(e) {
      formatTimeWithColon(this, true);
      validateTimeFormat(this);
      combineDateTime(this);
    });
    
    // 初始验证
    validateTimeFormat(input);
  });
  
  // 日期变更时更新隐藏字段
  dateInputs.forEach(function(dateInput) {
    dateInput.addEventListener('change', function() {
      const baseId = dateInput.id.replace('-date', '');
      const timeInput = document.getElementById(baseId + '-time');
      if (timeInput) {
        combineDateTime(timeInput);
      }
    });
  });
  
  // 初始化所有隐藏字段
  timeInputs.forEach(function(timeInput) {
    combineDateTime(timeInput);
  });
  
  // 表单提交前验证
  const forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      const timeInputs = form.querySelectorAll('.time-with-colon');
      let isValid = true;
      
      timeInputs.forEach(function(input) {
        if (!validateTimeFormat(input)) {
          isValid = false;
        }
        combineDateTime(input);
      });
      
      if (!isValid) {
        e.preventDefault();
        alert('请检查时间格式是否正确（HH:MM，24小时制）');
      }
    });
  });
});

/**
 * 格式化带冒号的时间输入
 * @param {HTMLInputElement} input - 时间输入框元素
 * @param {boolean} complete - 是否在失去焦点时完成格式化
 */
function formatTimeWithColon(input, complete = false) {
  let value = input.value.replace(/[^\d:]/g, ''); // 只保留数字和冒号
  
  // 如果为空，设置当前时间
  if (!value && complete) {
    const now = new Date();
    input.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    return;
  }
  
  // 处理已经包含冒号的情况
  if (value.includes(':')) {
    const parts = value.split(':');
    let hours = parts[0] || '';
    let minutes = parts[1] || '';
    
    // 限制小时和分钟的长度
    hours = hours.substring(0, 2);
    minutes = minutes.substring(0, 2);
    
    // 如果是完成格式化，确保小时和分钟都是两位数
    if (complete) {
      if (hours.length === 1) hours = '0' + hours;
      if (minutes.length === 1) minutes = '0' + minutes;
      
      // 验证并修正小时和分钟的值
      let hoursNum = parseInt(hours, 10);
      let minutesNum = parseInt(minutes, 10);
      
      if (isNaN(hoursNum) || hoursNum > 23) hoursNum = 0;
      if (isNaN(minutesNum) || minutesNum > 59) minutesNum = 0;
      
      hours = String(hoursNum).padStart(2, '0');
      minutes = String(minutesNum).padStart(2, '0');
    }
    
    input.value = hours + (hours && minutes ? ':' : '') + minutes;
  } else {
    // 处理没有冒号的情况
    const digits = value.replace(/\D/g, '');
    
    if (digits.length <= 2) {
      // 只有小时部分
      input.value = digits + (complete && digits ? ':00' : '');
    } else {
      // 有小时和分钟部分
      const hours = digits.substring(0, 2);
      const minutes = digits.substring(2, 4);
      input.value = hours + ':' + minutes;
    }
    
    // 如果是完成格式化，验证并修正值
    if (complete) {
      const parts = input.value.split(':');
      let hoursNum = parseInt(parts[0], 10);
      let minutesNum = parseInt(parts[1] || '0', 10);
      
      if (isNaN(hoursNum) || hoursNum > 23) hoursNum = 0;
      if (isNaN(minutesNum) || minutesNum > 59) minutesNum = 0;
      
      input.value = String(hoursNum).padStart(2, '0') + ':' + String(minutesNum).padStart(2, '0');
    }
  }
}

/**
 * 验证时间格式
 */
function validateTimeFormat(input) {
  const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
  const isValid = timeRegex.test(input.value);
  
  if (isValid) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
  } else {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
  }
  
  return isValid;
}

/**
 * 合并日期和时间到隐藏字段
 */
function combineDateTime(timeInput) {
  const baseId = timeInput.id.replace('-time', '');
  const dateInput = document.getElementById(baseId + '-date');
  const hiddenInput = document.getElementById(baseId);
  
  if (dateInput && hiddenInput) {
    const dateValue = dateInput.value;
    const timeValue = timeInput.value;
    
    if (dateValue && timeValue) {
      hiddenInput.value = `${dateValue} ${timeValue}`;
      console.log(`合并日期时间: ${hiddenInput.value}`);
    }
  }
} 