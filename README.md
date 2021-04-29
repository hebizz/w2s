### W2S 综合平台节点系统


**创建镜像**

1. [临时] 设置 asp/id, run.sh: ID
2. 修改Makefile
3. 使用`sudo make build`构建应用镜像


**依赖**

1、2.3.0版本wss获取ip依赖poseidon，如果没有安装波塞东，镜像容器会陷入restarting
2、2.3.0以上版本wss需要t-1.0.6以上版本AI镜像


**iotedge 发布**

- 全局替换`demo-name`为想取的应用名字
- 替换`worker_node`内的`image`为你创建上传的镜像名字
- 替换master_node内的`image`为云端应用的镜像名字
- 全局替换`J064b2d871`为你需要下发的设备的id