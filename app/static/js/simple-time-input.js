/**
 * 简单时间输入处理脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('简单时间输入处理脚本已加载');
  
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
  const timeInputs = document.querySelectorAll('.simple-time-input');
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
    
    // 失去焦点时格式化
    input.addEventListener('blur', function(e) {
      formatSimpleTime(this);
      validateSimpleTime(this);
      combineDateTime(this);
    });
    
    // 初始验证
    validateSimpleTime(input);
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
      const timeInputs = form.querySelectorAll('.simple-time-input');
      let isValid = true;
      
      timeInputs.forEach(function(input) {
        formatSimpleTime(input);
        if (!validateSimpleTime(input)) {
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
 * 格式化简单时间输入
 */
function formatSimpleTime(input) {
  let value = input.value.trim();
  
  // 如果为空，设置当前时间
  if (!value) {
    const now = new Date();
    input.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    return;
  }
  
  // 处理不同的输入格式
  
  // 只有数字的情况
  if (/^\d+$/.test(value)) {
    // 根据数字长度进行不同处理
    switch (value.length) {
      case 1: // 单个数字，假设是小时
        value = `0${value}:00`;
        break;
      case 2: // 两个数字，假设是小时
        value = `${value}:00`;
        break;
      case 3: // 三个数字，如130表示1:30
        value = `0${value.charAt(0)}:${value.substring(1)}`;
        break;
      case 4: // 四个数字，如1430表示14:30
        value = `${value.substring(0, 2)}:${value.substring(2)}`;
        break;
      default:
        // 超过4位数字，取前4位
        value = `${value.substring(0, 2)}:${value.substring(2, 4)}`;
    }
  } 
  // 已经包含冒号的情况
  else if (value.includes(':')) {
    const parts = value.split(':');
    let hours = parts[0].trim();
    let minutes = (parts[1] || '').trim();
    
    // 确保小时是两位数
    if (hours.length === 1) {
      hours = `0${hours}`;
    } else if (hours.length > 2) {
      hours = hours.substring(0, 2);
    }
    
    // 确保分钟是两位数
    if (minutes.length === 0) {
      minutes = '00';
    } else if (minutes.length === 1) {
      minutes = `${minutes}0`;
    } else if (minutes.length > 2) {
      minutes = minutes.substring(0, 2);
    }
    
    value = `${hours}:${minutes}`;
  }
  // 其他情况，尝试提取数字
  else {
    const digits = value.replace(/\D/g, '');
    if (digits.length === 0) {
      value = '00:00';
    } else if (digits.length <= 2) {
      value = `${digits.padStart(2, '0')}:00`;
    } else {
      value = `${digits.substring(0, 2)}:${digits.substring(2, 4).padEnd(2, '0')}`;
    }
  }
  
  // 验证小时和分钟的范围
  const parts = value.split(':');
  let hours = parseInt(parts[0], 10);
  let minutes = parseInt(parts[1], 10);
  
  if (isNaN(hours) || hours > 23) hours = 0;
  if (isNaN(minutes) || minutes > 59) minutes = 0;
  
  // 设置最终格式化的值
  input.value = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

/**
 * 验证时间格式
 */
function validateSimpleTime(input) {
  const value = input.value.trim();
  const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
  const isValid = timeRegex.test(value);
  
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