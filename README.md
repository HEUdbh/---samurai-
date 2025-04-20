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


#系统部署说明
克隆仓库
git clone https://github.com/HEUdbh/---samurai-.git

用IDE打开，启动虚拟环境，进入VUE项目目录输入：
npm run dev启动前端代码
进入django项目文件，输入
python manage.py runserver  启动项目后端程序

检查前后端时候有报错信息，没有报错信息等浏览器打开前端项目启动后返回的地址，按照页面提示操作即可

#文件说明
上传的视频文件限制为MP4文件格式
上传的txt文件为一行四个数字，依次为：x,y,w,h
用英文逗号隔开没有空格

注意：返回的处理好的视频如果浏览器加载不出来，就点击下载查看，或者到django项目目录中的media文件夹查看
