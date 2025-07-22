/**
 * 日期选择器与手动时间输入结合的处理脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('日期选择器与手动时间输入处理脚本已加载');
  
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
  
  // 设置时间分隔符位置
  const timeInputContainers = document.querySelectorAll('.time-input-container');
  timeInputContainers.forEach(function(container) {
    const timeInput = container.querySelector('.time-input');
    const separator = container.querySelector('.time-separator');
    
    // 调整分隔符位置
    adjustSeparatorPosition(timeInput, separator);
    
    // 窗口大小改变时重新调整
    window.addEventListener('resize', function() {
      adjustSeparatorPosition(timeInput, separator);
    });
  });
  
  // 设置当前时间为默认值
  const timeInputs = document.querySelectorAll('.time-input');
  timeInputs.forEach(function(input) {
    if (!input.value) {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      
      const defaultValue = `${hours}${minutes}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名时间输入框'} 设置默认值: ${defaultValue}`);
    }
    
    // 添加输入限制，只允许数字
    input.addEventListener('keypress', function(e) {
      const key = e.key;
      // 只允许输入数字
      if (!/^\d$/.test(key)) {
        e.preventDefault();
      }
    });
    
    // 粘贴事件处理
    input.addEventListener('paste', function(e) {
      e.preventDefault();
      const pasteData = (e.clipboardData || window.clipboardData).getData('text');
      // 提取所有数字
      const numbers = pasteData.replace(/\D/g, '');
      // 只取前4位数字
      const validNumbers = numbers.substring(0, 4);
      // 插入到当前位置
      const start = this.selectionStart;
      const end = this.selectionEnd;
      const currentValue = this.value;
      const newValue = currentValue.substring(0, start) + validNumbers + currentValue.substring(end);
      // 确保总长度不超过4
      this.value = newValue.substring(0, 4);
      // 更新光标位置
      this.selectionStart = this.selectionEnd = Math.min(start + validNumbers.length, 4);
      // 验证并格式化
      validateTimeFormat(input);
      combineDateTime(input);
    });
    
    // 添加时间格式验证
    input.addEventListener('input', function(e) {
      validateTimeFormat(e.target);
    });
    
    input.addEventListener('blur', function(e) {
      formatTimeInput(e.target);
      combineDateTime(input);
    });
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
      const timeInputs = form.querySelectorAll('.time-input');
      let isValid = true;
      
      timeInputs.forEach(function(input) {
        if (!validateTimeFormat(input)) {
          isValid = false;
        }
        combineDateTime(input);
      });
      
      if (!isValid) {
        e.preventDefault();
        alert('请检查时间格式是否正确（HHMM，24小时制）');
      }
    });
  });
});

/**
 * 调整分隔符位置
 */
function adjustSeparatorPosition(timeInput, separator) {
  if (!timeInput || !separator) return;
  
  // 获取输入框的宽度和字体大小
  const inputStyle = window.getComputedStyle(timeInput);
  const fontSize = parseFloat(inputStyle.fontSize);
  
  // 设置分隔符位置，在第2个和第3个字符之间
  separator.style.left = '50%';
  separator.style.marginLeft = '0px';
  separator.style.fontSize = fontSize + 'px';
}

/**
 * 验证时间格式
 */
function validateTimeFormat(input) {
  // 检查是否为4位数字
  const value = input.value.trim();
  const isValid = /^\d{4}$/.test(value);
  
  // 检查小时和分钟是否有效
  let hoursValid = false;
  let minutesValid = false;
  
  if (isValid) {
    const hours = parseInt(value.substring(0, 2), 10);
    const minutes = parseInt(value.substring(2, 4), 10);
    
    hoursValid = hours >= 0 && hours <= 23;
    minutesValid = minutes >= 0 && minutes <= 59;
  }
  
  const finalValid = isValid && hoursValid && minutesValid;
  
  if (finalValid) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
  } else {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
  }
  
  return finalValid;
}

/**
 * 格式化时间输入
 */
function formatTimeInput(input) {
  let value = input.value.trim();
  
  // 如果为空，设置当前时间
  if (!value) {
    const now = new Date();
    input.value = `${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
    return;
  }
  
  // 移除所有非数字字符
  value = value.replace(/\D/g, '');
  
  // 根据数字长度进行格式化
  switch (value.length) {
    case 1: // 单个数字，假设是小时
      value = `0${value}00`;
      break;
    case 2: // 两个数字，假设是小时
      value = `${value}00`;
      break;
    case 3: // 三个数字，前面补0
      value = `0${value}`;
      break;
    default:
      // 确保只有4位数字
      value = value.substring(0, 4);
  }
  
  // 验证小时和分钟
  let hours = parseInt(value.substring(0, 2), 10);
  let minutes = parseInt(value.substring(2, 4), 10);
  
  // 修正无效值
  if (hours > 23) hours = 23;
  if (minutes > 59) minutes = 59;
  
  // 重新格式化
  input.value = `${String(hours).padStart(2, '0')}${String(minutes).padStart(2, '0')}`;
  validateTimeFormat(input);
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
    
    if (dateValue && timeValue && timeValue.length === 4) {
      // 将HHMM格式转换为HH:MM格式
      const hours = timeValue.substring(0, 2);
      const minutes = timeValue.substring(2, 4);
      const formattedTime = `${hours}:${minutes}`;
      
      hiddenInput.value = `${dateValue} ${formattedTime}`;
      console.log(`合并日期时间: ${hiddenInput.value}`);
    }
  }
} 