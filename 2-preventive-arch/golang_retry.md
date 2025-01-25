# Golang 中的重试库

我们以 Golang 常见的重试库（[github.com/avast/retry-go/v4](http://github.com/avast/retry-go/v4)）为例说明，`retry-go` 提供了灵活的选项，可以满足各种重试需求。

### 1. 基本用法

```go
package main

import (
    "errors"
    "fmt"
    "github.com/avast/retry-go/v4"
)

func main() {
    err := retry.Do(func() error {
        // 尝试执行的代码，默认10次
        fmt.Println("Trying...")
        return errors.New("temporary error")
    })
    if err != nil {
        fmt.Printf("Final error: %v\n", err)
    }
}
```

### 说明

- `retry.Do` 会重复执行提供的函数，直到成功或达到默认重试次数。

---

### 2. 自定义重试次数和延迟

```go
err := retry.Do(
    func() error {
        return errors.New("an error occurred")
    },
    retry.Attempts(5),         // 尝试 5 次
    retry.DelayType(retry.FixedDelay), // 使用固定延迟
    retry.Delay(2 * time.Second), // 每次重试之间等待 2 秒
)
```

---

### 3. 使用条件来控制重试

```go
err := retry.Do(
    func() error {
        return errors.New("non-retriable error")
    },
    retry.RetryIf(func(err error) bool {
        // 仅当错误符合条件时才重试
        return err.Error() == "temporary error"
    }),
)
```

---

### 4. 指数回退策略

```go
err := retry.Do(
    func() error {
        return errors.New("an error")
    },
    retry.DelayType(retry.BackOffDelay), // 使用指数回退延迟
)
```

---

### 5. 使用上下文控制

```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

err := retry.Do(
    func() error {
        return errors.New("operation failed")
    },
    retry.Context(ctx), // 使用上下文控制超时
)
```

---

### 6. 自定义错误处理函数

```go
err := retry.Do(
    func() error {
        return errors.New("error example")
    },
    retry.OnRetry(func(n uint, err error) {
        fmt.Printf("Attempt %d: %v\n", n+1, err)
    }),
)
```

---

### 7. 多个选项组合

```go
err := retry.Do(
    func() error {
        return errors.New("example error")
    },
    retry.Attempts(3),
    retry.Delay(1*time.Second),
    retry.MaxJitter(500*time.Millisecond), // 增加抖动
)

```