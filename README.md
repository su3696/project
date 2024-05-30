# 基于文心一言的微信公众号聊天系统

# 介绍
  本项目是基于文心一言的微信公众号聊天系统，该系统实现了将百度文心一言大模型接入微信公众号的聊天系统中。

# 运行项目
## 1.准备微信公众平台账号
  进入微信公众平台主页（https://mp.weixin.qq.com/?token=&lang=zh_CN ），选择立刻注册，选择订阅号，依次填写好注册消息，这样成功申请了一个订阅号。
![image](https://github.com/su3696/project/blob/main/images/1.png)

  进入微信公众号基本设置界面，需要自行填写白名单，url，token，随机生成密钥，开发者密码(AppSecret)重置后可见
  
![image](https://github.com/su3696/project/blob/main/images/3.png)
## 2.准备云服务器
  根据云服务器地址填写微信设置，并在防火墙中打开8080端口。
  
## 3.python环境安装
  ```bash
    #安装必要依赖
    yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make libffi-devel
    #下载源码包
    #国内服务器推荐手动下载上传到root目录
    wget https://www.python.org/ftp/python/3.8.1/Python-3.8.1.tgz
    #解压文件
    tar -zxvf Python-3.8.1.tgz
    #进入文件夹
    cd Python-3.8.1
    #配置安装位置
    ./configure prefix=/usr/local/python3
    #安装
    make && make install
```
## 4.项目部署
  ```bash
    git clone https://github.com/su3696/project
```
## 5.配置config.json文件
微信设置对应填写，文心一言相关需要进入百度智能云官网获取（https://cloud.baidu.com/ ）
![image](https://github.com/su3696/project/blob/main/images/4.png)

## 6.启动项目
```bash
  nohup python3 start.py & tail -f nohup.out
```


