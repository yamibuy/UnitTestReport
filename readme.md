# unittestreport介绍

## 说明
本项目是在unittestreport的基础上增加了截图功能。在生成的最终的报告中可以看到截图，并支持多图切换。原项目地址：https://github.com/musen123/UnitTestReport
![sceen shot button](docs/img/screen-shot-1.png)
![view sceen shot](docs/img/screen-shot-2.png)

上传到pypi:

python setup.py sdist bdist_wheel

twine upload dist/*

修改setup.py文件，将版本号修改为最新的版本号

##  1、什么是unittestreport
unittestreport是基于unittest开发的的一个功能扩展库，关于unittestreport最初在开发的时候，最初只是计划开发一个unittest生成html测试报告的模块，所以起名叫做unittestreport。在开发的过程中结合使用者的反馈，慢慢的扩展了更多的功能进去。后续还会持续的扩展和开发一些新的功能，目前实现了以下功能：

- HTML测试报告生成
- unittest数据驱动
- 测试用例失败重运行
- 多线程并发执行用例
- 发送测试结果及报告到邮箱
- 测试结果推送到钉钉
- 测试结构推送到企业微信

## 2、安装unittestreport

unittestreport是基于python3.6开发的，安装前请确认你的python版本>3.6

- **安装命令**

    `pip install unittestreport`
- 说明：原报告模板中的CDN站点失效了，已在`1.4.2`版中进行了更换，如果生成的报告样式和图表丢失，请升级unittestreport版本`pip install unittestreport==1.4.2`



## 3、使用文档

使用文档地址：https://unittestreport.readthedocs.io/en/latest/



### 使用问题及维护：

- ##### 开发者：木森

- ##### WeChat:musen9111

- ##### 大家在使用过程中发现bug,以及使用过程中有什么问题，可以联系我










