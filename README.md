# ---samurai-
基于samurai的可视化系统，实现视频文件中选定目标的追踪，增加了可视化界面，易于操作简介易上手。
# 系统环境配置说明
本项目基于samurai设计，环境配置也是基于samurai进行的
这里给出samurai文档信息，请先参照那里的配置信息完成模型环境的搭建
在下载完GPU驱动后一定先去验证一下是否安装到位，检查流程可以在shell中输入以下命令进行
```
import torch
print(torch.__version__) # 输出 PyTorch 版本
print(torch.cuda.is_available()) # 检查 CUDA 是否可用，可用为Ture
print(torch.version.cuda) # 输出 CUDA 版本
```

注意：环境需要为整个项目配置（模型和后端程序均在虚拟环境中运行）
