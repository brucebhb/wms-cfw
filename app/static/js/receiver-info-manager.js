/**
 * 收货人信息管理器
 * 负责自动填充联络窗口和地址信息
 */
class ReceiverInfoManager {
    constructor() {
        this.warehouseData = {};
        this.isLoaded = false;
        this.init();
    }

    init() {
        console.log('🚀 收货人信息管理器初始化...');
        this.loadWarehouseData();
    }

    // 从API加载收货人信息
    async loadWarehouseData() {
        try {
            console.log('📡 开始加载收货人数据...');
            const response = await fetch('/api/receivers');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📦 API返回数据:', data);
            
            if (data.success && data.receivers) {
                // 转换API返回的格式
                this.warehouseData = {};
                data.receivers.forEach(receiver => {
                    this.warehouseData[receiver.warehouse_name] = {
                        contact: receiver.contact,
                        address: receiver.address
                    };
                });
                console.log('✅ 收货人数据加载成功:', this.warehouseData);
            } else {
                console.warn('⚠️ API返回数据格式错误，使用默认数据');
                this.loadDefaultData();
            }
        } catch (error) {
            console.error('❌ API调用失败:', error);
            console.log('🔄 使用默认收货人数据');
            this.loadDefaultData();
        }
        
        this.isLoaded = true;
        this.setupEvents();
    }

    // 加载默认收货人数据
    loadDefaultData() {
        this.warehouseData = {
            '平湖仓': {
                contact: '邬斌林/13641486964    钟文广/15113440547',
                address: '广东省东莞市凤岗镇凤平路1号,车辆进盛辉物流园左转22-23号码头车夫网仓库'
            },
            '昆山仓': {
                contact: '耿和兵/15287003539    黄新平/13543408533',
                address: '江苏省苏州市昆山普洛斯淀山湖物流园东门进去左转B7仓库码头'
            },
            '成都仓': {
                contact: '韩胜/17602866878    余苗/18328621911',
                address: '成都市青白江区远洋物流 2楼7-128'
            },
            '凭祥北投仓': {
                contact: '早班: 林飞威/17620431231 刘国宽/18776738925 晚班:莫显友/19377029961 凌廷忠/17776550065',
                address: '凭祥市凭祥镇北投跨境物流中心B8-3至B8-4门'
            },
            '凭祥保税仓': {
                contact: '李安章/18178680331   谭俊杰/17625737807',
                address: '凭祥市友谊镇卡凤村卡防屯友谊关口岸凭祥综合保税区卡凤物流加工区B4-1'
            },
            '春疆货场': {
                contact: '金英/84-971886919    石辉远/18685570447',
                address: '广西凭祥市谅山春疆货场'
            }
        };
        console.log('📋 默认收货人数据已加载');
    }

    // 设置事件监听器
    setupEvents() {
        console.log('🔧 设置收货人信息事件监听器...');
        
        // 始发仓选择器
        const originWarehouse = document.getElementById('originWarehouse');
        if (originWarehouse) {
            originWarehouse.addEventListener('change', (e) => this.handleOriginChange(e));
            this.setInitialValue('originWarehouse', 'originContact', 'originAddress');
        }
        
        // 目的仓选择器
        const destinationWarehouse = document.getElementById('destinationWarehouse');
        if (destinationWarehouse) {
            destinationWarehouse.addEventListener('change', (e) => this.handleDestinationChange(e));
            this.setInitialValue('destinationWarehouse', 'destinationContact', 'destinationAddress');
        }
        
        console.log('✅ 收货人信息事件监听器设置完成');
    }

    // 设置初始值
    setInitialValue(warehouseSelectId, contactFieldId, addressFieldId) {
        const warehouseSelect = document.getElementById(warehouseSelectId);
        const contactField = document.getElementById(contactFieldId);
        const addressField = document.getElementById(addressFieldId);
        
        if (warehouseSelect && contactField && addressField) {
            const selectedWarehouse = warehouseSelect.value;
            if (selectedWarehouse && this.warehouseData[selectedWarehouse]) {
                contactField.value = this.warehouseData[selectedWarehouse].contact;
                addressField.value = this.warehouseData[selectedWarehouse].address;
                console.log(`📝 已设置 ${selectedWarehouse} 的初始信息`);
            }
        }
    }

    // 处理始发仓变化
    handleOriginChange(event) {
        const warehouse = event.target.value;
        this.updateWarehouseInfo(warehouse, 'originContact', 'originAddress', '始发仓');
    }

    // 处理目的仓变化
    handleDestinationChange(event) {
        const warehouse = event.target.value;
        this.updateWarehouseInfo(warehouse, 'destinationContact', 'destinationAddress', '目的仓');
    }

    // 更新仓库信息
    updateWarehouseInfo(warehouse, contactFieldId, addressFieldId, type) {
        const contactField = document.getElementById(contactFieldId);
        const addressField = document.getElementById(addressFieldId);
        
        if (contactField && addressField) {
            if (warehouse && this.warehouseData[warehouse]) {
                contactField.value = this.warehouseData[warehouse].contact;
                addressField.value = this.warehouseData[warehouse].address;
                console.log(`✅ 已更新${type}信息: ${warehouse}`);
            } else {
                contactField.value = '';
                addressField.value = '';
                console.log(`🔄 已清空${type}信息`);
            }
        }
    }

    // 获取仓库信息
    getWarehouseInfo(warehouseName) {
        return this.warehouseData[warehouseName] || null;
    }

    // 检查是否已加载
    isDataLoaded() {
        return this.isLoaded;
    }
}

// 全局实例
let receiverInfoManager = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保页面元素已加载
    setTimeout(() => {
        receiverInfoManager = new ReceiverInfoManager();
        
        // 将实例暴露到全局，方便其他脚本使用
        window.receiverInfoManager = receiverInfoManager;
    }, 100);
});

// 导出给其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReceiverInfoManager;
}
