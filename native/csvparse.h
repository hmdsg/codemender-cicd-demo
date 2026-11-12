#ifndef CSVPARSE_H
#define CSVPARSE_H

#include <stddef.h>

/* 費目名として格納できる最大バイト数（終端 NUL を含む）。 */
#define MAX_FIELD_LEN 64

typedef struct {
    char name[MAX_FIELD_LEN];
    long amount_jpy;
} expense_row_t;

/* ヘッダ行の先頭カラム名を out へ取り出す。成功で 0、失敗で -1。 */
int parse_header(const char *line, char *out, size_t out_size);

/* "<費目>,<金額>" 形式の行をパースする。失敗時は NULL。 */
expense_row_t *parse_row(const char *line);

void free_row(expense_row_t *row);

#endif /* CSVPARSE_H */
