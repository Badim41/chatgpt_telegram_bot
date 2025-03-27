
def fix_markdown(text: str, to_fix: list) -> [str, str]:
    stack = {}  # Храним количество открытых тегов
    fixed_lines = []
    lines = text.split("\n")

    for tag in to_fix:
        stack[tag] = 0

    for line in lines:
        for tag in to_fix:
            if line.count(tag) % 2 == 1:  # Нечетное количество - проблема
                stack[tag] += 1

        fixed_lines.append(line)

    # Закрываем оставшиеся незакрытые теги
    added_tag = None
    for tag, count in stack.items():
        if count % 2 == 1:
            added_tag = tag
            if fixed_lines:
                fixed_lines[-1] += tag
            else:
                fixed_lines.append(tag)

    # print("added_tag", added_tag)
    return added_tag, "\n".join(fixed_lines)


def soft_wraps(text, max_length=20, split_threshold=10):
    final_result = ""
    for stream_result in soft_wraps_stream_base(source_gen=text,
                                                max_length=max_length,
                                                split_threshold=split_threshold):
        final_result = stream_result
    return final_result


def limit_soft_wraps_stream(source_gen, max_length=3950, split_threshold=3000,
                            min_length_yield=0, func_each_yield=None):
    """
    Ограничивает генератор, выдавая минимум min_length_yield символов за раз.
    Если накоплено меньше требуемого количества символов, данные сохраняются в буфере.

    Параметр func_each_yield позволяет изменить минимальный порог для следующего yield.
    Например, при min_length_yield=2 и func_each_yield=lambda x: x*2:
      - 1-й yield: минимум 2 символа,
      - 2-й yield: минимум 4 символа,
      - 3-й yield: минимум 8 символа.
    """
    try:
        buffer_length_last = 0
        current_min_length = min_length_yield
        chunk = None
        for chunk in soft_wraps_stream_base(source_gen=source_gen,
                                            max_length=max_length,
                                            split_threshold=split_threshold):
            buffer_length = len(''.join(chunk))
            while buffer_length - buffer_length_last >= current_min_length:
                yield chunk
                buffer_length_last = buffer_length
                if func_each_yield is not None:
                    current_min_length = func_each_yield(current_min_length)
        # Выдаём остаток, если он есть
        if chunk:
            yield chunk
    except Exception as e:
        print(f"Error: {e}")


def soft_wraps_stream_base(source_gen, max_length=3950, split_threshold=3000):
    buffer = ""
    result = []
    added_tag_last = None

    for segment in source_gen:
        new_length = len(segment)  # Длина новых символов
        buffer += segment

        # Если добавлено достаточно символов, чтобы удовлетворить min_length
        if True:
            # stream buffer
            _, fixed_buffer = fix_markdown(buffer, ["**", "```"])
            result.append(None)  # add stream buffer
            result[-1] = fixed_buffer  # set stream buffer
            yield result  # yield stream buffer
            result = result[:-1]  # remove stream buffer

        while len(buffer) >= max_length:
            split_index = max_length  # По умолчанию разрезаем на max_length символах
            if len(buffer) > split_threshold:
                newline_index = buffer.rfind("\n", split_threshold, max_length)
                if newline_index != -1:
                    split_index = newline_index + 1  # Включаем \n в первую часть

            added_tag, fixed_markdown_buffer = fix_markdown(buffer[:split_index], ["**", "```"])

            if added_tag_last:
                fixed_markdown_buffer = added_tag_last + fixed_markdown_buffer
                added_tag = None

            result.append(fixed_markdown_buffer)
            yield result
            added_tag_last = f"{added_tag}\n" if added_tag == "```" else added_tag
            buffer = buffer[split_index:]

    if buffer:
        if added_tag_last:
            buffer = added_tag_last + buffer
        result.append(buffer)

    if result:
        yield result