---
layout: post
title: memcached
---
## memcached
- brew install memcached `mac安装`
- brew services start memcached `启动`
- brew services stop memcached `关闭`
- telnet localhost 11211 `连接`

## memcached 命令参数

参数 | 用法
---|---
key | key
flags | 键值外的信息，32位
expiratin time | 时间，0永远 
bytes | 字节数 
value | 存储的值，位于第二行

```
//set 命令用于向缓存添加新的键值对。如果键已经存在，则之前的值将被替换
set userid 0 0 5
12345

//add 仅当缓存中不存在键时，add 命令才会向缓存中添加一个键值对。如果缓存中已经存在键，则之前的值将仍然保持相同，并且您将获得响应 NOT_STORED
add companyId 0 0 3
564

//replace 仅当键已经存在时，replace 命令才会替换缓存中的键。如果缓存中不存在键，那么您将从 memcached 服务器接受到一条 NOT_STORED 响应
replace accountId 0 0 5
55555

//get 命令用于检索与之前添加的键值对相关的值。您将使用 get 执行大多数检索操作
get userId

//delete 命令用于删除 memcached 中的任何现有值。您将使用一个键调用 delete，如果该键存在于缓存中，则删除该值。如果不存在，则返回一条 NOT_FOUND 消息
delete userId

//gets 命令的功能类似于基本的 get 命令。两个命令之间的差异在于，gets 返回的信息稍微多一些：64 位的整型值非常像名称/值对的 “版本” 标识符
gets userId

//cas（check 和 set）是一个非常便捷的 memcached 命令，用于设置名称/值对的值（如果该名称/值对在您上次执行 gets 后没有更新过）。它使用与 set 命令相类似的语法，但包括一个额外的值：gets 返回的额外值。
cas userId 0 0 5 6
33333

//stats 转储所连接的 memcached 实例的当前统计数据
//比较有参考意义的值，get_hits（命中缓存次） 的数值除以 cmd_gets（总次数），命中率
```



