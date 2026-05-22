'use client';

import { Badge, Group } from '@mantine/core';
import { useState } from 'react';

export type Tag = {
  value: string;
  label: string;
};

type TagCloudProps = {
  tags: Tag[];
  defaultValue?: string;
  onChange?: (value: string) => void;
};

export function TagCloud({ tags, defaultValue = '', onChange }: TagCloudProps) {
  const [active, setActive] = useState(defaultValue);

  function handleClick(value: string) {
    setActive(value);
    onChange?.(value);
  }

  return (
    <Group gap={6} wrap="wrap">
      {tags.map((tag) => (
        <Badge
          key={tag.value}
          variant={active === tag.value ? 'light' : 'outline'}
          color={active === tag.value ? 'rdg-orange' : 'dark'}
          radius="sm"
          size="sm"
          ff="monospace"
          style={{ cursor: 'pointer', userSelect: 'none' }}
          onClick={() => handleClick(tag.value)}
        >
          {tag.label}
        </Badge>
      ))}
    </Group>
  );
}
