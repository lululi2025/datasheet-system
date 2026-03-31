"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ProductLine } from "@/types/database";

interface ProductSummary {
  id: string;
  model_name: string;
  subtitle: string;
  full_name: string;
  current_version: string;
  product_image: string;
  sheet_last_modified: string | null;
  sheet_last_editor: string | null;
  updated_at: string;
  product_line_id: string;
  product_line: { name: string; label: string; category: string };
  image_readiness: { total: number; ready: number };
}

interface DashboardContentProps {
  productLines: ProductLine[];
  products: ProductSummary[];
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function ImageReadinessBadge({
  readiness,
}: {
  readiness: { total: number; ready: number };
}) {
  if (readiness.total === 0) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        No images
      </Badge>
    );
  }
  const allReady = readiness.ready === readiness.total;
  return (
    <Badge variant={allReady ? "default" : "secondary"}>
      {readiness.ready}/{readiness.total}
    </Badge>
  );
}

function ProductTable({ products }: { products: ProductSummary[] }) {
  if (products.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground">
        No products found in this product line.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Model</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Version</TableHead>
          <TableHead>Last Edited</TableHead>
          <TableHead>Edited By</TableHead>
          <TableHead>Images</TableHead>
          <TableHead className="w-[100px]">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {products.map((product) => (
          <TableRow key={product.id}>
            <TableCell>
              <Link
                href={`/product/${product.model_name}`}
                className="font-medium text-engenius-blue hover:underline"
              >
                {product.model_name}
              </Link>
            </TableCell>
            <TableCell className="max-w-[300px] truncate text-sm text-muted-foreground">
              {product.subtitle || product.full_name}
            </TableCell>
            <TableCell>
              <Badge variant="outline" className="tabular-nums">
                v{product.current_version}
              </Badge>
            </TableCell>
            <TableCell className="text-sm tabular-nums">
              {formatDate(product.sheet_last_modified ?? product.updated_at)}
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {product.sheet_last_editor ?? "—"}
            </TableCell>
            <TableCell>
              <ImageReadinessBadge readiness={product.image_readiness} />
            </TableCell>
            <TableCell>
              <Link
                href={`/preview/${product.model_name}`}
                target="_blank"
                className="text-xs text-engenius-blue hover:underline"
              >
                Preview
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function DashboardContent({
  productLines,
  products,
}: DashboardContentProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("all");
  const [syncing, setSyncing] = useState(false);

  const filteredProducts =
    activeTab === "all"
      ? products
      : products.filter((p) => p.product_line_id === activeTab);

  async function handleSync() {
    setSyncing(true);
    try {
      const res = await fetch("/api/sync", { method: "POST" });
      const data = await res.json();
      if (data.ok) {
        const totalSynced = data.results.reduce(
          (sum: number, r: { synced: string[] }) => sum + r.synced.length,
          0
        );
        alert(`Sync complete: ${totalSynced} products updated.`);
        router.refresh();
      } else {
        alert(`Sync failed: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      alert(`Sync failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSyncing(false);
    }
  }

  const totalProducts = products.length;
  const imagesReady = products.filter(
    (p) => p.image_readiness.total > 0 && p.image_readiness.ready === p.image_readiness.total
  ).length;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums">
              {totalProducts}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Product Lines
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums">
              {productLines.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Images Ready
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums">
              {imagesReady}/{totalProducts}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs + table */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="all">All ({products.length})</TabsTrigger>
            {productLines.map((pl) => {
              const count = products.filter(
                (p) => p.product_line_id === pl.id
              ).length;
              return (
                <TabsTrigger key={pl.id} value={pl.id}>
                  {pl.label} ({count})
                </TabsTrigger>
              );
            })}
          </TabsList>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSync}
            disabled={syncing}
          >
            {syncing ? "Syncing..." : "Sync from Sheets"}
          </Button>
        </div>

        <TabsContent value={activeTab} className="mt-4">
          <div className="rounded-lg border bg-card">
            <ProductTable products={filteredProducts} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
