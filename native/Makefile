# C パーサ用のビルド定義。
#
# AddressSanitizer を常に有効にする。境界外アクセスがあれば実行時に
# heap-buffer-overflow として即座に検出される。
#
#   make build   ... バイナリを作る
#   make test    ... 正常系テストを実行（cm build から呼ばれる）
#   make clean
#
# コンパイラは cc (macOS: clang / Cloud Shell: gcc) を既定で使う。
# 明示したい場合は  make CC=clang  のように指定する。

CFLAGS  ?= -g -O1 -std=c11 -Wall -Wextra \
           -fsanitize=address -fno-omit-frame-pointer
LDFLAGS ?= -fsanitize=address

# 出力先。phony ターゲット名 (build) と衝突させないこと。
OUT_DIR  := out
BINARIES := $(OUT_DIR)/import_csv $(OUT_DIR)/test_csvparse

.PHONY: all build test clean

all: build

build: $(BINARIES)

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

$(OUT_DIR)/import_csv: import_csv.c csvparse.c csvparse.h | $(OUT_DIR)
	$(CC) $(CFLAGS) -o $@ import_csv.c csvparse.c $(LDFLAGS)

$(OUT_DIR)/test_csvparse: test_csvparse.c csvparse.c csvparse.h | $(OUT_DIR)
	$(CC) $(CFLAGS) -o $@ test_csvparse.c csvparse.c $(LDFLAGS)

test: $(OUT_DIR)/test_csvparse
	./$(OUT_DIR)/test_csvparse

clean:
	rm -rf $(OUT_DIR)
