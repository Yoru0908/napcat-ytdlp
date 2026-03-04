# 🤝 贡献指南

感谢你对 NapCat Video Bot 项目的关注！我们欢迎所有形式的贡献。

## 📋 贡献方式

### 🐛 报告 Bug

1. 检查 [Issues](https://github.com/yourusername/napcat-ytdlp/issues) 确认 Bug 未被报告
2. 使用 [Bug Report 模板](https://github.com/yourusername/napcat-ytdlp/issues/new?template=bug_report.md) 创建 Issue
3. 提供详细信息：
   - 操作系统和版本
   - Python 版本
   - 错误日志
   - 重现步骤

### 💡 功能建议

1. 检查 [Issues](https://github.com/yourusername/napcat-ytdlp/issues) 确认建议未被提出
2. 使用 [Feature Request 模板](https://github.com/yourusername/napcat-ytdlp/issues/new?template=feature_request.md) 创建 Issue
3. 详细描述功能需求和使用场景

### 🔧 代码贡献

#### 开发环境设置

```bash
# 1. Fork 项目并克隆
git clone https://github.com/yourusername/napcat-ytdlp.git
cd napcat-ytdlp

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 安装 pre-commit hooks
pre-commit install
```

#### 开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

2. **编写代码**
   - 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码风格
   - 添加必要的注释和文档字符串
   - 确保代码通过所有测试

3. **测试**
   ```bash
   # 运行单元测试
   pytest tests/
   
   # 代码格式检查
   black app/
   flake8 app/
   
   # 类型检查
   mypy app/
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型说明：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(download): add support for bilibili live recording

- Implement live stream detection
- Add retry mechanism for network issues
- Update documentation

Closes #123
```

## 📝 代码规范

### Python 代码风格

- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [flake8](https://flake8.pycqa.org/) 进行代码检查
- 使用 [mypy](https://mypy.readthedocs.io/) 进行类型检查

### 文档字符串

使用 Google 风格的文档字符串：

```python
def download_video(url: str, output_path: str) -> bool:
    """下载视频文件。
    
    Args:
        url: 视频URL地址
        output_path: 输出文件路径
        
    Returns:
        下载成功返回 True，失败返回 False
        
    Raises:
        NetworkError: 网络连接异常
        DownloadError: 下载过程异常
    """
    pass
```

### 测试

- 为新功能编写单元测试
- 测试覆盖率应保持在 80% 以上
- 使用描述性的测试名称

```python
def test_download_video_success():
    """测试视频下载成功场景。"""
    # Given
    url = "https://example.com/video.mp4"
    output_path = "/tmp/test_video.mp4"
    
    # When
    result = download_video(url, output_path)
    
    # Then
    assert result is True
    assert os.path.exists(output_path)
```

## 🏗️ 项目结构

```
napcat-ytdlp/
├── app/                    # 主应用代码
│   ├── handlers/          # 消息处理器
│   ├── executor/          # 下载执行器
│   └── utils/             # 工具函数
├── tests/                  # 测试代码
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/         # 测试数据
├── docs/                  # 文档
├── scripts/               # 脚本工具
└── examples/              # 示例代码
```

## 🎯 贡献重点领域

我们特别欢迎在以下领域的贡献：

### 🚀 功能增强

- [ ] 支持更多视频平台
- [ ] 添加视频转码功能
- [ ] 实现批量下载
- [ ] 添加下载进度推送
- [ ] 支持用户权限管理

### 🗂️ 存储后端

- [ ] 添加更多云存储支持
- [ ] 实现存储空间管理
- [ ] 添加文件去重功能

### 🌐 Web 界面

- [ ] 改进 Web UI 设计
- [ ] 添加实时进度显示
- [ ] 实现任务管理界面
- [ ] 添加统计图表

### 📱 移动端支持

- [ ] 添加 PWA 支持
- [ ] 优化移动端体验
- [ ] 实现推送通知

## 🔍 代码审查

### 审查要点

1. **功能正确性**
   - 代码是否按预期工作
   - 是否有充分的测试覆盖

2. **代码质量**
   - 代码是否清晰易读
   - 是否遵循项目规范
   - 是否有潜在的性能问题

3. **安全性**
   - 是否有安全漏洞
   - 敏感信息是否正确处理
   - 输入验证是否充分

4. **文档**
   - 是否有必要的注释
   - 文档是否更新
   - API 文档是否完整

### PR 审查流程

1. 自动化检查通过
2. 至少一个维护者审查
3. 解决所有审查意见
4. 通过 CI/CD 检查
5. 合并到主分支

## 📧 联系方式

- 📧 邮件：your-email@example.com
- 💬 QQ群：123456789
- 🐛 Issues：[GitHub Issues](https://github.com/yourusername/napcat-ytdlp/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/yourusername/napcat-ytdlp/discussions)

## 🏆 贡献者

感谢所有为项目做出贡献的开发者！

### 贡献者列表

- [@yourusername](https://github.com/yourusername) - 项目创建者
- 添加你的名字...

### 如何成为贡献者

1. 提交有意义的 Pull Request
2. 积极参与社区讨论
3. 帮助回答其他用户的问题
4. 改进项目文档

---

## 📄 许可证

通过贡献代码，你同意你的贡献将在 [MIT License](LICENSE) 下授权。

---

再次感谢你的贡献！🎉
