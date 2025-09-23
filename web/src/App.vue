<template>
  <div class="container">
    <div class="header">
      <h1>因果分析系统</h1>
      <p>输入问题描述，系统将帮助您分析可能的原因</p>
      <button @click="startAction">点击开始分析！</button>
    </div>

    <div class="content">
      <div class="section">
        <div class="section-title">
          <i>📊</i> 分析路径
        </div>
        <div class="text-display">{{ reasonPath || '分析路径将在此显示...' }}</div>
      </div>

      <div class="section">
        <div class="section-title">
          <i>🔍</i> 可能原因
        </div>
        <div class="button-list">
          <button
            v-for="choice in choices"
            :key="choice"
            class="choice-button"
            :class="{ selected: selectedChoices.includes(choice) }"
            @click="toggleChoice(choice)"
          >
            {{ choice }}
          </button>
          <div v-if="choices.length === 0" class="text-display" style="min-height: auto; text-align: center;">
            暂无选项，请先进行分析
          </div>
        </div>

        <button
          class="action-button"
          style="margin-top: 15px;"
          :disabled="selectedChoices.length === 0 || isAnalyzing"
          @click="submitAnalysis"
        >
          <span v-if="isAnalyzing" class="loading"></span>
          {{ isAnalyzing ? '分析中...' : '提交分析' }}
        </button>
      </div>

      <div class="section">
        <div class="section-title">
          <i>💡</i> 问题描述
        </div>
        <div class="input-section">
          <input
            type="text"
            class="text-input"
            v-model="userInput"
            placeholder="请输入您遇到的问题描述..."
            :disabled="isFinal"
          >
          <button
            class="action-button"
            :disabled="!userInput || isGenerating"
            @click="generateGraph"
          >
            <span v-if="isGenerating" class="loading"></span>
            {{ isGenerating ? '生成中...' : '开始分析' }}
          </button>
        </div>

        <div class="status-message" :class="messageType">{{ message }}</div>
      </div>
    </div>

    <div class="footer">
      因果分析系统 &copy; 2023 - 基于Vue.js开发
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'CauseAnalysis',
  data() {
    return {
      userInput: '',
      reasonPath: '',
      choices: [],
      selectedChoices: [],
      isFinal: false,
      isGenerating: false,
      isAnalyzing: false,
      message: '',
      messageType: '',
      agent_id: '',
      user_id: ''
    };
  },
  methods: {
    // 显示消息
    showMessage(text, type) {
      this.message = text;
      this.messageType = type;
      setTimeout(() => {
        this.message = '';
        this.messageType = '';
      }, 5000);
    },

    // 模拟API调用 - 在实际应用中替换为真实的API端点
    mockGenerateGraphAPI(input) {
      return new Promise((resolve) => {
        setTimeout(() => {
          // 模拟API响应
          resolve({
            reason_path: `问题分析路径：\n1. 识别问题: "${input}"\n2. 初步分析: 系统检测到多个可能原因\n3. 请从下列选项中选择相关原因进行深入分析`,
            choices: [
              "网络连接问题",
              "系统配置错误",
              "资源不足",
              "软件版本不兼容",
              "权限问题",
              "数据损坏"
            ]
          });
        }, 1500);
      });
    },

    async startAction() {
      try {
        // 实际应用中替换为真实的API调用
        const response = await axios.get('http://localhost:5000/start');
        // const response = await this.mockGenerateGraphAPI(this.userInput);
        this.agent_id = response.data.agent_id
        this.user_id = response.data.user_id
        this.showMessage('创建用户id成功', 'success');
      } catch (error) {
        console.error('尝试启动时出错:', error);
        this.showMessage('尝试创建用户id出错，请稍后重试', 'error');
      }
    },
    // 模拟根因分析API调用
    mockRootCauseAnalyseAPI(selectedItems) {
      return new Promise((resolve) => {
        setTimeout(() => {
          // 模拟API响应
          const isFinalResult = selectedItems.length > 2; // 简单模拟最终结果的条件

          if (isFinalResult) {
            resolve({
              is_final: true,
              analyse_summary: `根据您的选择，系统分析已完成。\n根本原因可能是: ${selectedItems.join(' 和 ')}。\n建议解决方案: 检查相关配置并重启服务。`
            });
          } else {
            resolve({
              is_final: false,
              reason_path: `已选择: ${selectedItems.join(', ')}\n继续分析路径：\n1. 验证所选原因\n2. 检查系统日志\n3. 进行进一步诊断`,
              choices: [
                "检查系统日志",
                "验证配置参数",
                "测试网络连接",
                "查看资源使用情况",
                "检查依赖服务状态"
              ]
            });
          }
        }, 2000);
      });
    },

    // 生成分析图
    async generateGraph() {
      if (!this.userInput) {
        this.showMessage('请输入问题描述', 'error');
        return;
      }

      this.isGenerating = true;
      this.showMessage('正在生成分析路径...', '');

      try {
        // 实际应用中替换为真实的API调用
        const response = await axios.post('http://localhost:5000/action/generate_graph', { context: this.userInput });
        // const response = await this.mockGenerateGraphAPI(this.userInput);

        // 更新数据
        this.reasonPath = response.reason_path;
        this.choices = response.choices;
        this.selectedChoices = [];
        this.isFinal = false;

        this.showMessage('分析路径生成成功！请从可能原因中选择相关项目。', 'success');
      } catch (error) {
        console.error('生成分析图时出错:', error);
        this.showMessage('生成分析图时出错，请稍后重试', 'error');
      } finally {
        this.isGenerating = false;
      }
    },

    // 切换选择项
    toggleChoice(choice) {
      const index = this.selectedChoices.indexOf(choice);
      if (index > -1) {
        this.selectedChoices.splice(index, 1);
      } else {
        this.selectedChoices.push(choice);
      }
    },

    // 提交分析
    async submitAnalysis() {
      if (this.selectedChoices.length === 0) {
        this.showMessage('请至少选择一个可能原因', 'error');
        return;
      }

      this.isAnalyzing = true;
      this.showMessage('正在进行根因分析...', '');

      try {
        // 实际应用中替换为真实的API调用
        const response = await axios.post('http://localhost:5000/action/root_cause_analyse', { choices: this.selectedChoices });
        // const response = await this.mockRootCauseAnalyseAPI(this.selectedChoices);

        if (response.is_final) {
          // 最终结果，更新输入框
          this.userInput = response.analyse_summary;
          this.isFinal = true;
          this.showMessage('分析完成！已生成最终分析摘要。', 'success');
        } else {
          // 非最终结果，更新路径和选项
          this.reasonPath = response.reason_path;
          this.choices = response.choices;
          this.selectedChoices = [];
          this.showMessage('分析进行中，请继续选择相关选项。', 'success');
        }
      } catch (error) {
        console.error('分析过程中出错:', error);
        this.showMessage('分析过程中出错，请稍后重试', 'error');
      } finally {
        this.isAnalyzing = false;
      }
    }
  }
}
</script>

<style scoped>
/* 样式已移至全局style.css文件 */
</style>