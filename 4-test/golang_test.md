# 基础测试

以下是在 Go 语言中新增一个单元测试（Unit Test，简称 UT）的示例：

新建 xxx_test.go，内容如下：

```
package main

import (
    "testing"
)

// add 函数，将两个整数相加
func add(a, b int) int {
    return a + b
}

// TestAdd 是 add 函数的单元测试函数
func TestAdd(t *testing.T) {
    // 测试用例 1
    result := add(2, 3)
    if result!= 5 {
        t.Errorf("add(2, 3) = %d, want 5", result)
    }

    // 测试用例 2
    result = add(-1, 1)
    if result!= 0 {
        t.Errorf("add(-1, 1) = %d, want 0", result)
    }

    // 测试用例 3
    result = add(0, 0)
    if result!= 0 {
        t.Errorf("add(0, 0) = %d, want 0", result)
    }
}
```

代码解释和使用说明：

1. 包的导入：
- 首先，我们导入了 testing 包，这是 Go 语言标准库中用于编写单元测试的包。
2. 被测试函数：
- add 函数是我们要测试的函数，它接受两个整数 a 和 b 作为输入，并返回它们的和。
3. 单元测试函数的命名：
- 单元测试函数的命名必须以 Test 开头，后面跟要测试的函数名，例如 TestAdd 是 add 函数的测试函数。它接收一个 *testing.T 类型的参数 t，用于报告测试结果。
4. 测试用例：
- 在 TestAdd 函数中，我们定义了几个测试用例：
- 对于 add(2, 3)，我们期望结果是 5。如果结果不是 5，我们使用 t.Errorf 函数来报告错误，输出错误信息。
- 对于 add(-1, 1)，我们期望结果是 0。同样，如果结果不符合期望，使用 t.Errorf 输出错误信息。
- 对于 add(0, 0)，我们期望结果是 0。

执行某个目录及子目录下所有的测试用例：

```
go test ./...
```

该命令会自动查找以 _test.go 结尾的文件，并执行其中的 Test 开头的测试函数。如果测试通过，将显示 PASS；如果有测试失败，将显示 FAIL 并给出详细的错误信息。


注意事项：
- 每个测试用例应该是独立的，不依赖于其他测试用例的结果或状态。
- 对于复杂的函数，可能需要更多不同的测试用例，包括正常情况、边界情况和异常情况的测试。
- 在 t.Errorf 中，提供清晰的错误信息，以便在测试失败时能快速定位问题。
总之，通过编写单元测试，可以帮助你验证代码的正确性，提高代码的质量和可维护性，同时在代码修改时可以快速检查是否引入了新的问题。

运行 UT 其它实用小技巧：
1. 加上 -v 可以打印更详细的输出。
2. 加上 -race 可以检查潜在的并发问题。
3. 运行某个test文件下的某个特定用例.
```
 go test -gcflags=all=-l -cover -coverprofile=coverage.out -race -v -coverpkg=./... **cmdx/cmd_test.go cmdx/cmd.go** **-test.run TestLog**
```
上面的命令，将运行 cmd_test.go 的 TestLog 这个用例。
4. 想要覆盖率，加上-coverprofile=c.out：
```
go test pkg/election/* -v -coverprofile=c.out
go tool cover -html=c.out -o=tag.html # 生成html文件
```
5. 加上 -count=1 可以 disable cache，避免使用缓存而不实际运行测试用例。
# 利用 Mock 进行测试
Golang 有很多常见的 Mock 库，我们这里以字节跳动开源的 mockey 为例，给出一个示例：

```
package mock

import (
	"fmt"
	"testing"

	. "github.com/bytedance/mockey"
	. "github.com/smartystreets/goconvey/convey"
)

// Simple function
func Foo(in string) string {
	return in
}

// Function method (value receiver)
type A struct{}

func (a A) Foo(in string) string { return in }

// Function method (pointer receiver)
type B struct{}

func (b *B) Foo(in string) string { return in }

// Value
var Bar = 0

func TestMockDemo(t *testing.T) {

	PatchConvey("Function mocking", t, func() {
		Mock(Foo).Return("c").Build()         // mock function
		So(Foo("anything"), ShouldEqual, "c") // assert `Foo` is mocked
	})

	PatchConvey("Method mocking (value receiver)", t, func() {
		Mock(A.Foo).Return("c").Build()              // mock method
		So(new(A).Foo("anything"), ShouldEqual, "c") // assert `A.Foo` is mocked
	})

	PatchConvey("Method mocking (pointer receiver)", t, func() {
		Mock((*B).Foo).Return("c").Build() // mock method
		b := &B{}
		So(b.Foo("anything"), ShouldEqual, "c") // assert `*B.Foo` is mocked
	})

	PatchConvey("Variable mocking", t, func() {
		MockValue(&Bar).To(1)   // mock variable
		So(Bar, ShouldEqual, 1) // assert `Bar` is mocked
	})

	// the mocks are released automatically outside `PatchConvey`
	fmt.Println(Foo("a"))        // a
	fmt.Println(new(A).Foo("b")) // b
	fmt.Println(Bar)             // 0
}

```
# 利用 Failpoint 进行故障注入

绝大部分情况下，使用 Mock 库足以应对大部分的 UT 场景。Mock 库对原代码（被测试的正式代码）几乎没有侵入性，这意味着我们不需要对正式代码进行改造来实现 mock。
但有一些场景，我们希望程序在更为真实的环境中运行，并且动态地注入一些随机故障。这时候，failpoint 库就可以发挥作用。
我们来看一个实际的例子：


```
package main

import (
	"errors"
	"fmt"
	"reflect"

	"github.com/pingcap/failpoint"
)

type Empty struct {
}

func Cmd() error {
	if val, _err_ := failpoint.Eval(FailpointName(Empty{}, "Cmd", "ErrorX")); _err_ == nil {
		if tmpstr, ok := val.(string); ok {
			return errors.New(tmpstr)
		}
	}
	return nil
}

func FailpointName(packageStruct any, funcName string, name string) string {
	return reflect.TypeOf(packageStruct).PkgPath() + ":" + funcName + ":" + name
}

func main() {
	// 激活故障点
	failpoint.Enable(FailpointName(Empty{}, "Cmd", "ErrorX"), "return(\"error when test\")")
	// 返回特定的 error 'error when test' 。这里 hardcode 了错误信息，而实际上这个错误信息可以由外部传入，达到更为灵活的故障注入的目的。
	fmt.Println(Cmd())
	// 取消故障点
	failpoint.Disable(FailpointName(Empty{}, "Cmd", "ErrorX"))
	// 返回 nil
	fmt.Println(Cmd())
	fmt.Println(FailpointName(Empty{}, "Cmd", "ErrorX"))

}


```

Failpoint 的机制和 mock 不同，体现在：
1. failpoint 的代码同样也是生产代码的一部分，只是平时故障注入点（failpoint.Eval）并不会被激活。仅在做一些故障注入测试的时候，可以灵活地注入各种故障。
2. 不需要特殊的编译选项。