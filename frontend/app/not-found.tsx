import Link from "next/link";
import { Button } from "./components/ui/button";
export default function NotFound() {
  return <div className="panel mx-auto my-16 max-w-lg p-10 text-center"><p className="eyebrow">404 · Not found</p><h1 className="my-4 text-2xl">This page is not available</h1><p className="mb-6 text-sm text-muted-foreground">Search for a ticker or return to your workspace.</p><Button asChild><Link href="/">Back to Explore</Link></Button></div>;
}
