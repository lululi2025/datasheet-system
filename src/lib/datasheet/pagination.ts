/**
 * Spec page pagination & column balancing logic.
 * Ported from the Python pdf_generator.py.
 */

interface Section {
  category: string;
  items: { label: string; value: string }[];
}

interface SpecPage {
  left: Section[];
  right: Section[];
}

// Height estimates (in pt) for page layout
const PAGE_HEIGHT = 792;
const TOP_BAR_HEIGHT = 21;
const SPEC_TITLE_HEIGHT = 42; // title + margin
const BOTTOM_MARGIN = 40; // page number + safety margin
const AVAILABLE_HEIGHT =
  PAGE_HEIGHT - TOP_BAR_HEIGHT - SPEC_TITLE_HEIGHT - BOTTOM_MARGIN;

const CATEGORY_HEADER_HEIGHT = 18;
const SPEC_ROW_HEIGHT = 18;

function estimateSectionHeight(section: Section): number {
  return CATEGORY_HEADER_HEIGHT + section.items.length * SPEC_ROW_HEIGHT;
}

function balanceColumns(sections: Section[]): SpecPage {
  const totalItems = sections.reduce((sum, s) => sum + s.items.length, 0);
  const target = totalItems / 2;

  const left: Section[] = [];
  const right: Section[] = [];
  let count = 0;
  let splitDone = false;

  for (const section of sections) {
    if (!splitDone && count + section.items.length <= target + 2) {
      left.push(section);
      count += section.items.length;
    } else {
      splitDone = true;
      right.push(section);
    }
  }

  return { left, right };
}

export function splitIntoPages(sections: Section[]): SpecPage[] {
  if (!sections.length) return [{ left: [], right: [] }];

  const pages: SpecPage[] = [];
  const remaining = [...sections];

  while (remaining.length > 0) {
    const left: Section[] = [];
    const right: Section[] = [];
    let leftH = 0;
    let rightH = 0;
    let i = 0;

    // Fill left column
    while (i < remaining.length) {
      const sh = estimateSectionHeight(remaining[i]);
      if (leftH + sh <= AVAILABLE_HEIGHT || left.length === 0) {
        left.push(remaining[i]);
        leftH += sh;
        i++;
      } else {
        break;
      }
    }

    // Fill right column
    while (i < remaining.length) {
      const sh = estimateSectionHeight(remaining[i]);
      if (rightH + sh <= AVAILABLE_HEIGHT || right.length === 0) {
        right.push(remaining[i]);
        rightH += sh;
        i++;
      } else {
        break;
      }
    }

    pages.push({ left, right });
    remaining.splice(0, i);
  }

  // If only one page, balance columns evenly
  if (pages.length === 1) {
    return [balanceColumns(sections)];
  }

  return pages;
}
