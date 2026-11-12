/*
 * csvparse.c -- 経費 CSV の行パーサ
 *
 * 経費精算 API は、銀行から送られてくる CSV 明細を取り込むために
 * このネイティブパーサを使う（想定）。入力は外部由来である。
 *
 * ※ 意図的に脆弱な教材コード。どこにもデプロイしないこと。
 */

#include "csvparse.h"

#include <stdlib.h>
#include <string.h>

/*
 * ヘッダ行から列名を取り出す。
 *
 * こちらは境界チェックを正しく行っている実装のお手本。
 * 取り出せる長さを MAX_FIELD_LEN - 1 で必ず打ち切る。
 */
int parse_header(const char *line, char *out, size_t out_size) {
    if (line == NULL || out == NULL || out_size == 0) {
        return -1;
    }

    const char *comma = strchr(line, ',');
    size_t field_len = (comma != NULL) ? (size_t)(comma - line) : strlen(line);

    if (field_len > out_size - 1) {
        field_len = out_size - 1;
    }

    memcpy(out, line, field_len);
    out[field_len] = '\0';
    return 0;
}

/*
 * 明細行 "<費目>,<金額>" をパースして expense_row_t に詰める。
 *
 * 費目は expense_row_t.name (MAX_FIELD_LEN バイト) に格納する。
 */
expense_row_t *parse_row(const char *line) {
    if (line == NULL) {
        return NULL;
    }

    expense_row_t *row = calloc(1, sizeof(*row));
    if (row == NULL) {
        return NULL;
    }

    const char *comma = strchr(line, ',');
    if (comma == NULL) {
        free(row);
        return NULL;
    }

    size_t name_len = (size_t)(comma - line);

    memcpy(row->name, line, name_len);
    row->name[name_len] = '\0';

    row->amount_jpy = strtol(comma + 1, NULL, 10);
    return row;
}

void free_row(expense_row_t *row) { free(row); }
