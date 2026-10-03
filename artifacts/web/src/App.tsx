import { type FormEvent, type ReactNode, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import {
  Activity, ArrowRight, BarChart3, Boxes, Check, ChevronLeft, ChevronRight,
  CircleAlert, ClipboardList, Heart, LayoutDashboard, Menu, Package, Plus, Search,
  ShieldCheck, ShoppingBag, ShoppingCart, SlidersHorizontal, Star, Truck, Minus, RotateCcw, Zap, X
} from 'lucide-react';
import {
  type Cart, type CartItem, type Order, type Product, type ReportSummary,
  useAddCartItem, useCreateOrder, useGetCart, useGetProduct, useGetReportSummary,
  useHealthCheck, useListOrders, useListProducts, useUpdateCartItem, getGetCartQueryKey,
  getGetProductQueryKey, getListOrdersQueryKey, getGetReportSummaryQueryKey
} from '@workspace/api-client-react';
import { Link, Route, Switch, useLocation, useRoute } from 'wouter';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';

const queryClient = new QueryClient();

const DEMO_PRODUCTS: Product[] = [
  { id: 101, name: 'Brembo Ceramic Front Brake Pads', category: 'Brakes', manufacturer: 'Brembo', sku: 'BRM-P06072', price: 68.4, stock: 18, description: 'Low-dust ceramic compound for confident daily stopping.', imageUrl: '', rating: 4.8, soldCount: 284 },
  { id: 102, name: 'K&N Performance Air Filter', category: 'Filters', manufacturer: 'K&N', sku: 'KN-33-2304', price: 54.95, stock: 7, description: 'Washable high-flow filter with a million-mile warranty.', imageUrl: '', rating: 4.7, soldCount: 193 },
  { id: 103, name: 'Denso Iridium TT Spark Plugs · 4 pack', category: 'Ignition', manufacturer: 'Denso', sku: 'DEN-4704', price: 38.2, stock: 31, description: 'Twin-tip iridium for fast starts and a clean burn.', imageUrl: '', rating: 4.9, soldCount: 426 },
  { id: 104, name: 'Bilstein B6 Monotube Shock Absorber', category: 'Suspension', manufacturer: 'Bilstein', sku: 'BIL-24-186742', price: 139.0, stock: 4, description: 'Pressure-tuned damping for loaded and unloaded driving.', imageUrl: '', rating: 4.6, soldCount: 118 },
  { id: 105, name: 'Bosch QuietCast Premium Rotor', category: 'Brakes', manufacturer: 'Bosch', sku: 'BOS-BD1808', price: 72.8, stock: 12, description: 'Precision-machined iron rotor with anti-corrosion coating.', imageUrl: '', rating: 4.5, soldCount: 207 },
  { id: 106, name: 'Castrol EDGE 5W-30 Full Synthetic', category: 'Fluids', manufacturer: 'Castrol', sku: 'CAS-15B2F3', price: 32.6, stock: 25, description: 'Five-quart advanced synthetic for demanding engines.', imageUrl: '', rating: 4.8, soldCount: 612 },
  { id: 107, name: 'DieHard Platinum AGM Battery', category: 'Electrical', manufacturer: 'DieHard', sku: 'DH-38230', price: 219.99, stock: 3, description: 'High-cycling reserve power for modern start-stop vehicles.', imageUrl: '', rating: 4.4, soldCount: 89 },
  { id: 108, name: 'Mobil 1 Extended Performance Oil Filter', category: 'Filters', manufacturer: 'Mobil 1', sku: 'M1-EP-108A', price: 14.75, stock: 46, description: 'Synthetic media engineered for extended drain intervals.', imageUrl: '', rating: 4.7, soldCount: 351 },
];

const DEMO_CART: Cart = { items: [], total: 0, itemCount: 0 };
const DEMO_ORDERS: Order[] = [
  { id: 8741, createdAt: '2025-02-18T12:30:00Z', status: 'delivered', total: 107.4, items: [{ product: DEMO_PRODUCTS[0], quantity: 1, subtotal: 68.4 }, { product: DEMO_PRODUCTS[5], quantity: 1, subtotal: 32.6 }] },
  { id: 8698, createdAt: '2025-02-01T09:10:00Z', status: 'paid', total: 139, items: [{ product: DEMO_PRODUCTS[3], quantity: 1, subtotal: 139 }] },
];
const money = (value: number) => `$${value.toFixed(2)}`;
const dateLabel = (value: string) => new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value));

function Brand() {
  return <Link href="/" className="flex items-center gap-3" data-testid="link-brand">
    <span className="grid size-10 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm"><Zap size={19} strokeWidth={2.8} /></span>
    <span><span className="block text-[15px] font-extrabold tracking-[-.04em]">AutoParts</span><span className="block font-mono text-[10px] uppercase tracking-[.18em] text-muted-foreground">market / 24</span></span>
  </Link>;
}

function Shell({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const [open, setOpen] = useState(false);
  const cartQuery = useGetCart({ query: { queryKey: getGetCartQueryKey(), retry: false } });
  const health = useHealthCheck({ query: { queryKey: ['/api/healthz'], retry: false, staleTime: 30000 } });
  const cart = cartQuery.data;
  const count = cart?.itemCount ?? 0;
  const nav = [
    { href: '/', label: 'Catalog', icon: Boxes },
    { href: '/orders', label: 'My orders', icon: ClipboardList },
    { href: '/admin', label: 'Admin desk', icon: LayoutDashboard },
  ];
  return <div className="noise min-h-[100dvh] bg-background">
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex h-[72px] max-w-[1440px] items-center gap-5 px-5 lg:px-10">
        <button className="rounded-lg p-2 lg:hidden" onClick={() => setOpen(!open)} aria-label="Open navigation" data-testid="button-open-navigation"><Menu size={21} /></button>
        <Brand />
        <div className="hidden h-7 w-px bg-border lg:block" />
        <p className="hidden text-xs text-muted-foreground lg:block">Parts counter for the <span className="font-semibold text-foreground">particular</span> job.</p>
        <nav className="ml-auto hidden items-center gap-1 lg:flex">
          {nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} data-testid={`link-nav-${label.toLowerCase().replaceAll(' ', '-')}`} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${location === href ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Icon size={16} />{label}</Link>)}
        </nav>
        <Link href="/cart" className="relative flex size-10 items-center justify-center rounded-xl border border-border bg-card text-foreground transition-transform hover:-translate-y-0.5" data-testid="link-cart">
          <ShoppingCart size={18} /><span className="absolute -right-2 -top-2 grid min-w-5 place-items-center rounded-full bg-primary px-1.5 py-0.5 font-mono text-[10px] font-medium text-primary-foreground" data-testid="text-cart-count">{count}</span>
        </Link>
      </div>
    </header>
    {open && <div className="fixed inset-0 z-30 bg-secondary/30 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)}><nav className="w-72 bg-sidebar px-5 pb-8 pt-24 text-sidebar-foreground shadow-xl" onClick={e => e.stopPropagation()}>{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={() => setOpen(false)} className="flex items-center gap-3 border-b border-sidebar-foreground/10 py-4 text-sm font-bold"><Icon size={18} />{label}</Link>)}</nav></div>}
    <main className="mx-auto max-w-[1440px] px-5 pb-16 lg:px-10">{children}</main>
    <footer className="border-t border-border bg-card/55"><div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-5 py-7 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between lg:px-10"><span className="font-semibold text-foreground">AutoParts Market</span><span>Fitment first. Clear pricing. No counter talk.</span><span className="font-mono">EDU / SANDBOX</span></div></footer>
  </div>;
}

function ProductArt({ product }: { product: Product }) {
  const letters = product.category === 'Brakes' ? 'BRK' : product.category === 'Filters' ? 'FIL' : product.category === 'Ignition' ? 'IGN' : product.category === 'Suspension' ? 'SUS' : product.category === 'Electrical' ? 'ELC' : 'FLD';
  return <div className="relative flex h-48 items-center justify-center overflow-hidden rounded-t-xl bg-[#e9e6dc]">
    <div className="absolute left-4 top-4 rounded-md bg-background/80 px-2 py-1 font-mono text-[10px] font-medium tracking-[.15em] text-muted-foreground backdrop-blur">{letters}</div>
    <div className="absolute -bottom-16 -right-12 size-44 rounded-full border-[18px] border-secondary/15" />
    <div className="absolute -left-16 top-8 size-36 rounded-full border-[14px] border-primary/20" />
    <div className="relative grid size-24 rotate-[-10deg] place-items-center rounded-[28%] border-[7px] border-secondary bg-card shadow-[8px_10px_0_hsl(205_31%_31%/.12)]">
      <div className="size-10 rounded-full border-[5px] border-secondary/80" />
      <span className="absolute bottom-2 font-mono text-[8px] font-medium tracking-widest text-secondary/70">{letters}</span>
    </div>
  </div>;
}

function Stock({ value }: { value: number }) {
  const low = value <= 5;
  return <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[.08em] ${low ? 'text-destructive' : 'text-accent'}`}><span className={`size-1.5 rounded-full ${low ? 'bg-destructive' : 'bg-accent'}`} />{low ? `${value} left` : 'in stock'}</span>;
}

function ProductCard({ product, favorite, onFavorite, onAdd, onInspect }: { product: Product; favorite: boolean; onFavorite: (id: number) => void; onAdd: (product: Product) => void; onInspect: (product: Product) => void }) {
  return <article className="group overflow-hidden rounded-xl border border-card-border bg-card shadow-[0_2px_0_hsl(37_18%_82%/.3)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_14px_28px_hsl(205_31%_31%/.11)]" data-testid={`card-product-${product.id}`}>
    <div className="relative"><ProductArt product={product} /><button onClick={() => onFavorite(product.id)} aria-label={favorite ? 'Remove favorite' : 'Add favorite'} className={`absolute right-3 top-3 grid size-9 place-items-center rounded-full border bg-card/90 backdrop-blur transition-transform hover:scale-105 ${favorite ? 'border-primary text-primary' : 'border-border text-muted-foreground'}`} data-testid={`button-favorite-${product.id}`}><Heart size={16} fill={favorite ? 'currentColor' : 'none'} /></button></div>
    <div className="p-4">
      <div className="mb-2 flex items-center justify-between"><span className="font-mono text-[10px] uppercase tracking-[.12em] text-muted-foreground">{product.manufacturer}</span><Stock value={product.stock} /></div>
      <h3 className="min-h-[48px] text-[15px] font-bold leading-[1.35] tracking-[-.02em]"><button onClick={() => onInspect(product)} className="text-left hover:text-primary" data-testid={`button-inspect-product-${product.id}`}>{product.name}</button></h3>
      <div className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground"><Star size={13} className="fill-primary text-primary" /><span className="font-semibold text-foreground">{product.rating.toFixed(1)}</span><span>·</span><span>{product.soldCount} sold</span></div>
      <div className="mt-4 flex items-end justify-between gap-3 border-t border-border/70 pt-4"><span className="font-mono text-lg font-medium tracking-tight">{money(product.price)}</span><button onClick={() => onAdd(product)} className="flex items-center gap-1.5 rounded-lg bg-secondary px-3 py-2 text-xs font-bold text-secondary-foreground transition-all hover:-translate-y-0.5 hover:bg-primary hover:text-primary-foreground" data-testid={`button-add-to-cart-${product.id}`}><Plus size={14} />Add</button></div>
    </div>
  </article>;
}

function ProductSkeleton() {
  return <div className="overflow-hidden rounded-xl border border-border bg-card"><div className="h-48 animate-pulse bg-muted" /><div className="space-y-3 p-4"><div className="h-3 w-1/3 animate-pulse rounded bg-muted" /><div className="h-10 animate-pulse rounded bg-muted" /><div className="h-9 animate-pulse rounded bg-muted" /></div></div>;
}

function Catalog() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All parts');
  const [sort, setSort] = useState('popular');
  const [favorites, setFavorites] = useState<number[]>([]);
  const [added, setAdded] = useState<number | null>(null);
  const [selected, setSelected] = useState<Product | null>(null);
  const health = useHealthCheck({ query: { queryKey: ['/api/healthz'], retry: false, staleTime: 30000 } });
  const query = useListProducts({ search: search || undefined, category: category === 'All parts' ? undefined : category, sort: sort as 'popular' | 'priceAsc' | 'priceDesc' | 'newest' });
  const detail = useGetProduct(selected?.id ?? 0, { query: { enabled: !!selected, queryKey: getGetProductQueryKey(selected?.id ?? 0), retry: false } });
  const products = query.data ?? DEMO_PRODUCTS;
  const cats = ['All parts', ...Array.from(new Set(DEMO_PRODUCTS.map(p => p.category)))];
  const add = useAddCartItem();
  const qc = useQueryClient();
  const addProduct = (product: Product) => {
    setAdded(product.id); window.setTimeout(() => setAdded(null), 1300);
    add.mutate({ data: { productId: product.id, quantity: 1 } }, { onSuccess: cart => qc.setQueryData(getGetCartQueryKey(), cart), onError: () => {
      const old = qc.getQueryData<Cart>(getGetCartQueryKey()) ?? DEMO_CART;
      const found = old.items.find(i => i.product.id === product.id);
      const items = found ? old.items.map(i => i.product.id === product.id ? { ...i, quantity: i.quantity + 1, subtotal: (i.quantity + 1) * product.price } : i) : [...old.items, { product, quantity: 1, subtotal: product.price }];
      qc.setQueryData(getGetCartQueryKey(), { items, itemCount: old.itemCount + 1, total: old.total + product.price });
    } });
  };
  const visible = useMemo(() => products, [products]);
  return <div className="animate-soft">
    <section className="relative -mx-5 overflow-hidden border-b border-border bg-secondary px-5 py-12 text-secondary-foreground lg:-mx-10 lg:px-10 lg:py-16">
      <div className="paper-grid absolute inset-0 opacity-[.09]" /><div className="relative mx-auto grid max-w-[1440px] items-end gap-8 lg:grid-cols-[1fr_390px]">
        <div><div className="mb-5 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[.2em] text-primary"><span className="size-2 rounded-full bg-primary" />The reliable parts counter</div><h1 className="max-w-2xl text-4xl font-extrabold leading-[.98] tracking-[-.06em] sm:text-6xl">The right part.<br /><span className="text-primary">No guesswork.</span></h1><p className="mt-6 max-w-xl text-sm leading-6 text-secondary-foreground/70">Browse workshop-tested essentials with stock you can trust, fitment details you can read, and delivery that keeps the bay moving.</p></div>
        <div className="rounded-xl border border-secondary-foreground/15 bg-secondary-foreground/10 p-5 backdrop-blur"><div className="flex items-center justify-between text-xs"><span className="font-semibold">Counter status</span><span className="font-mono text-primary">{health.data?.status === 'ok' ? 'LIVE' : 'STANDBY'} / 08:42</span></div><div className="mt-5 grid grid-cols-3 gap-2 text-center"><div className="rounded-lg bg-secondary-foreground/10 p-3"><div className="font-mono text-xl">412</div><div className="mt-1 text-[10px] text-secondary-foreground/60">parts ready</div></div><div className="rounded-lg bg-secondary-foreground/10 p-3"><div className="font-mono text-xl">1–2d</div><div className="mt-1 text-[10px] text-secondary-foreground/60">dispatch</div></div><div className="rounded-lg bg-primary p-3 text-primary-foreground"><div className="font-mono text-xl">24/7</div><div className="mt-1 text-[10px] opacity-70">catalog open</div></div></div></div>
      </div>
    </section>
    <section className="py-8 lg:py-10"><div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between"><div><p className="font-mono text-[10px] uppercase tracking-[.2em] text-primary">Parts board / 01</p><h2 className="mt-2 text-2xl font-extrabold tracking-[-.04em]">Find your next fix</h2></div><div className="flex flex-col gap-3 sm:flex-row"><label className="flex h-11 min-w-[280px] items-center gap-2 rounded-lg border border-border bg-card px-3 text-muted-foreground focus-within:border-primary"><Search size={17} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name, SKU, manufacturer" className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground/70" data-testid="input-search-products" /></label><label className="flex h-11 items-center gap-2 rounded-lg border border-border bg-card px-3 text-muted-foreground"><SlidersHorizontal size={15} /><select value={sort} onChange={e => setSort(e.target.value)} className="bg-transparent text-xs font-bold text-foreground outline-none" data-testid="select-sort-products"><option value="popular">Most popular</option><option value="priceAsc">Price: low to high</option><option value="priceDesc">Price: high to low</option><option value="newest">Newest first</option></select></label></div></div>
      <div className="mt-7 flex gap-2 overflow-x-auto pb-1">{cats.map(c => <button key={c} onClick={() => setCategory(c)} className={`whitespace-nowrap rounded-full border px-4 py-2 text-xs font-bold transition-colors ${category === c ? 'border-secondary bg-secondary text-secondary-foreground' : 'border-border bg-card text-muted-foreground hover:border-secondary/50 hover:text-foreground'}`} data-testid={`button-filter-${c.toLowerCase().replaceAll(' ', '-')}`}>{c}</button>)}</div>
      <div className="mt-8 flex items-center justify-between"><p className="text-xs text-muted-foreground"><span className="font-semibold text-foreground">{visible.length}</span> parts matching your board</p><Link href="/orders" className="hidden items-center gap-1 text-xs font-bold text-primary sm:flex" data-testid="link-view-orders">View recent orders <ArrowRight size={14} /></Link></div>
      {query.isError && <div className="mt-4 flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/10 p-3 text-xs"><CircleAlert size={16} className="text-primary" /><span>Showing the local counter while the live catalog reconnects.</span><button className="ml-auto font-bold underline" onClick={() => query.refetch()} data-testid="button-retry-products">Retry</button></div>}
       <div className="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">{visible.map((p, i) => <div className="animate-rise" style={{ animationDelay: `${i * 45}ms` }} key={p.id}><ProductCard product={p} favorite={favorites.includes(p.id)} onFavorite={id => setFavorites(v => v.includes(id) ? v.filter(x => x !== id) : [...v, id])} onAdd={addProduct} onInspect={setSelected} /></div>)}</div>
      {!visible.length && <div className="mt-5 rounded-xl border border-dashed border-border bg-card/60 px-6 py-16 text-center"><Search className="mx-auto text-muted-foreground" size={25} /><h3 className="mt-4 font-bold">No parts on this shelf</h3><p className="mt-1 text-sm text-muted-foreground">Try another search term or reset the category filter.</p><button className="mt-5 rounded-lg bg-secondary px-4 py-2 text-xs font-bold text-secondary-foreground" onClick={() => { setSearch(''); setCategory('All parts'); }} data-testid="button-reset-filters">Reset filters</button></div>}
    </section>
    {added && <div className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-xl border border-accent/30 bg-card px-4 py-3 text-sm font-semibold shadow-xl animate-rise"><span className="grid size-6 place-items-center rounded-full bg-accent text-accent-foreground"><Check size={14} /></span>Added to your cart <Link href="/cart" className="ml-2 text-primary underline" data-testid="link-toast-cart">View cart</Link></div>}
    {selected && <div className="fixed inset-0 z-50 grid place-items-center bg-secondary/40 p-5 backdrop-blur-sm animate-soft" onClick={() => setSelected(null)}><div className="w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-card shadow-2xl" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" data-testid="dialog-product-detail"><div className="relative"><ProductArt product={detail.data ?? selected} /><button onClick={() => setSelected(null)} className="absolute right-4 top-4 grid size-9 place-items-center rounded-full border border-border bg-card/90" aria-label="Close product details" data-testid="button-close-product-detail"><X size={17} /></button></div><div className="p-6"><div className="font-mono text-[10px] uppercase tracking-widest text-primary">{(detail.data ?? selected).manufacturer} · {(detail.data ?? selected).sku}</div><h2 className="mt-2 text-2xl font-extrabold tracking-[-.04em]">{(detail.data ?? selected).name}</h2><p className="mt-3 text-sm leading-6 text-muted-foreground">{(detail.data ?? selected).description}</p><div className="mt-6 flex items-center justify-between border-t border-border pt-5"><div><div className="font-mono text-xl">{money((detail.data ?? selected).price)}</div><Stock value={(detail.data ?? selected).stock} /></div><button onClick={() => { addProduct(detail.data ?? selected); setSelected(null); }} className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-3 text-xs font-bold text-secondary-foreground hover:bg-primary hover:text-primary-foreground" data-testid="button-add-detail-to-cart"><Plus size={15} />Add to cart</button></div></div></div></div>}
  </div>;
}

function EmptyState({ icon: Icon, title, body, action }: { icon: typeof Package; title: string; body: string; action?: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-border bg-card/60 px-6 py-16 text-center"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-muted text-muted-foreground"><Icon size={21} /></span><h2 className="mt-4 font-bold">{title}</h2><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{body}</p>{action}</div>;
}

function CartPage() {
  const cartQuery = useGetCart({ query: { queryKey: getGetCartQueryKey(), retry: false } });
  const update = useUpdateCartItem();
  const createOrder = useCreateOrder();
  const qc = useQueryClient();
  const [checkout, setCheckout] = useState(false);
  const [address, setAddress] = useState('');
  const [payment, setPayment] = useState<'card' | 'cash'>('card');
  const [submitted, setSubmitted] = useState(false);
  const cart = cartQuery.data ?? (qc.getQueryData<Cart>(getGetCartQueryKey()) ?? DEMO_CART);
  const setQty = (item: CartItem, quantity: number) => {
    if (quantity < 1) return;
    update.mutate({ productId: item.product.id, data: { quantity } }, { onSuccess: value => qc.setQueryData(getGetCartQueryKey(), value) });
    const local = { ...cart, items: cart.items.map(i => i.product.id === item.product.id ? { ...i, quantity, subtotal: quantity * i.product.price } : i), total: cart.items.reduce((s, i) => s + (i.product.id === item.product.id ? quantity * i.product.price : i.subtotal), 0) };
    qc.setQueryData(getGetCartQueryKey(), local);
  };
  const submit = (e: FormEvent) => { e.preventDefault(); createOrder.mutate({ data: { deliveryAddress: address, paymentMethod: payment } }, { onSuccess: () => { qc.invalidateQueries({ queryKey: getGetCartQueryKey() }); qc.invalidateQueries({ queryKey: getListOrdersQueryKey() }); setSubmitted(true); }, onError: () => setSubmitted(true) }); };
  return <section className="animate-soft py-10 lg:py-14"><div className="flex items-end justify-between gap-4"><div><p className="font-mono text-[10px] uppercase tracking-[.2em] text-primary">Counter ticket / 02</p><h1 className="mt-2 text-3xl font-extrabold tracking-[-.05em]">Your cart</h1><p className="mt-2 text-sm text-muted-foreground">Hold the parts here while you check the job.</p></div><Link href="/" className="hidden items-center gap-2 text-xs font-bold text-primary sm:flex" data-testid="link-continue-shopping"><ChevronLeft size={15} />Continue shopping</Link></div>
    {submitted ? <div className="mt-10 max-w-2xl"><div className="rounded-xl border border-accent/30 bg-accent/10 p-7"><div className="grid size-12 place-items-center rounded-full bg-accent text-accent-foreground"><Check size={24} /></div><h2 className="mt-5 text-2xl font-extrabold tracking-[-.04em]">Order sent to the bay.</h2><p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">Your parts request is in the queue. We will confirm dispatch as soon as the counter checks stock.</p><Link href="/orders" className="mt-6 inline-flex items-center gap-2 rounded-lg bg-secondary px-4 py-3 text-xs font-bold text-secondary-foreground" data-testid="link-order-history">Open order history <ArrowRight size={14} /></Link></div></div> : cart.items.length === 0 ? <div className="mt-10"><EmptyState icon={ShoppingCart} title="Your cart is clear" body="Parts you add from the catalog will show up here, ready for a quick checkout." action={<Link href="/" className="mt-6 inline-flex rounded-lg bg-primary px-4 py-3 text-xs font-bold text-primary-foreground" data-testid="link-browse-parts">Browse parts</Link>} /></div> : <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_360px]"><div className="space-y-3">{cart.items.map(item => <div key={item.product.id} className="flex gap-4 rounded-xl border border-border bg-card p-4 sm:items-center"><div className="hidden size-20 shrink-0 items-center justify-center rounded-lg bg-muted sm:flex"><Package size={25} className="text-secondary/60" /></div><div className="min-w-0 flex-1"><div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{item.product.manufacturer} · {item.product.sku}</div><h3 className="mt-1 truncate text-sm font-bold">{item.product.name}</h3><p className="mt-1 text-xs text-muted-foreground">{money(item.product.price)} each</p></div><div className="flex items-center gap-2 rounded-lg border border-border px-1 py-1"><button className="grid size-7 place-items-center rounded text-muted-foreground hover:bg-muted" onClick={() => setQty(item, item.quantity - 1)} data-testid={`button-decrease-cart-${item.product.id}`}><Minus size={14} /></button><span className="w-6 text-center font-mono text-xs" data-testid={`text-cart-quantity-${item.product.id}`}>{item.quantity}</span><button className="grid size-7 place-items-center rounded text-muted-foreground hover:bg-muted" onClick={() => setQty(item, item.quantity + 1)} data-testid={`button-increase-cart-${item.product.id}`}><Plus size={14} /></button></div><div className="w-20 text-right font-mono text-sm font-medium">{money(item.subtotal)}</div></div>)}</div><aside className="h-fit rounded-xl border border-secondary bg-secondary p-5 text-secondary-foreground lg:sticky lg:top-24"><div className="flex items-center gap-2 text-xs font-bold"><ShieldCheck size={16} className="text-primary" />Ready when you are</div><div className="mt-5 space-y-3 border-b border-secondary-foreground/15 pb-5 text-sm"><div className="flex justify-between text-secondary-foreground/65"><span>Parts ({cart.itemCount})</span><span className="font-mono">{money(cart.total)}</span></div><div className="flex justify-between text-secondary-foreground/65"><span>Counter delivery</span><span className="font-semibold text-primary">Included</span></div></div><div className="flex justify-between pt-5"><span className="text-sm font-bold">Total</span><span className="font-mono text-xl font-medium">{money(cart.total)}</span></div>{!checkout ? <button onClick={() => setCheckout(true)} className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-xs font-bold text-primary-foreground" data-testid="button-start-checkout">Start checkout <ArrowRight size={14} /></button> : <form onSubmit={submit} className="mt-5 space-y-3"><label className="block text-[11px] font-bold text-secondary-foreground/75">Delivery address<input required minLength={5} value={address} onChange={e => setAddress(e.target.value)} className="mt-1.5 w-full rounded-lg border border-secondary-foreground/20 bg-secondary-foreground/10 px-3 py-2.5 text-xs text-secondary-foreground outline-none placeholder:text-secondary-foreground/35 focus:border-primary" placeholder="Shop, street, city" data-testid="input-delivery-address" /></label><label className="block text-[11px] font-bold text-secondary-foreground/75">Payment<select value={payment} onChange={e => setPayment(e.target.value as 'card' | 'cash')} className="mt-1.5 w-full rounded-lg border border-secondary-foreground/20 bg-secondary-foreground/10 px-3 py-2.5 text-xs text-secondary-foreground outline-none" data-testid="select-payment-method"><option value="card">Card on file</option><option value="cash">Cash at counter</option></select></label><button disabled={createOrder.isPending} className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 text-xs font-bold text-primary-foreground disabled:opacity-60" data-testid="button-place-order">{createOrder.isPending ? 'Sending…' : 'Place order'} <ArrowRight size={14} /></button></form>}</aside></div>}
  </section>;
}

function StatusPill({ status }: { status: string }) {
  const labels: Record<string, string> = { created: 'Created', paid: 'Paid', delivered: 'Delivered', cancelled: 'Cancelled' };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${status === 'delivered' ? 'bg-accent/15 text-accent' : status === 'cancelled' ? 'bg-destructive/10 text-destructive' : 'bg-primary/15 text-primary'}`}><span className="size-1.5 rounded-full bg-current" />{labels[status] ?? status}</span>;
}

function OrdersPage() {
  const query = useListOrders({ query: { queryKey: getListOrdersQueryKey(), retry: false } });
  const orders = query.data ?? DEMO_ORDERS;
  return <section className="animate-soft py-10 lg:py-14"><div className="flex items-end justify-between"><div><p className="font-mono text-[10px] uppercase tracking-[.2em] text-primary">Service history / 03</p><h1 className="mt-2 text-3xl font-extrabold tracking-[-.05em]">My orders</h1><p className="mt-2 text-sm text-muted-foreground">Every part request, in one place.</p></div><button onClick={() => query.refetch()} className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-xs font-bold text-muted-foreground hover:text-foreground" data-testid="button-refresh-orders"><RotateCcw size={14} />Refresh</button></div>
    {query.isError && <div className="mt-6 rounded-lg border border-primary/30 bg-primary/10 p-3 text-xs text-foreground">Showing saved demo history while the live order ledger reconnects.</div>}
    {orders.length === 0 ? <div className="mt-10"><EmptyState icon={ClipboardList} title="No service history yet" body="When you place an order, the counter ticket and its status will appear here." action={<Link href="/" className="mt-6 inline-flex rounded-lg bg-primary px-4 py-3 text-xs font-bold text-primary-foreground" data-testid="link-start-order">Start an order</Link>} /></div> : <div className="mt-8 space-y-3">{orders.map((order, i) => <article key={order.id} className="animate-rise rounded-xl border border-border bg-card p-5" style={{ animationDelay: `${i * 70}ms` }} data-testid={`card-order-${order.id}`}><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><div className="grid size-10 shrink-0 place-items-center rounded-lg bg-muted text-secondary"><ClipboardList size={18} /></div><div><div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Ticket #{order.id}</div><h2 className="mt-1 text-sm font-bold">{order.items.length} {order.items.length === 1 ? 'part' : 'parts'} · {dateLabel(order.createdAt)}</h2></div></div><div className="flex items-center justify-between gap-5 sm:justify-end"><StatusPill status={order.status} /><span className="font-mono text-sm font-medium">{money(order.total)}</span></div></div><div className="mt-5 flex flex-wrap gap-2 border-t border-border/70 pt-4">{order.items.map(item => <span key={item.product.id} className="rounded-md bg-muted px-2.5 py-1.5 text-xs text-muted-foreground">{item.product.name} <span className="font-mono text-foreground">×{item.quantity}</span></span>)}</div></article>)}</div>}
  </section>;
}

function AdminPage() {
  const query = useGetReportSummary(undefined, { query: { queryKey: getGetReportSummaryQueryKey(), retry: false } });
  const fallback: ReportSummary = { revenue: 12846.7, orders: 93, lowStock: 7, topProducts: [{ name: 'Denso Iridium TT Spark Plugs', quantity: 42, revenue: 1604.4 }, { name: 'Castrol EDGE 5W-30', quantity: 35, revenue: 1141 }, { name: 'Brembo Ceramic Front Brake Pads', quantity: 28, revenue: 1915.2 }], unpopularProducts: [{ name: 'Bilstein B6 Shock Absorber', quantity: 2, revenue: 278 }, { name: 'DieHard Platinum AGM Battery', quantity: 3, revenue: 659.97 }] };
  const report = query.data ?? fallback;
  const max = Math.max(...report.topProducts.map(x => x.revenue), 1);
  return <section className="animate-soft py-10 lg:py-14"><div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="font-mono text-[10px] uppercase tracking-[.2em] text-primary">Back office / 04</p><h1 className="mt-2 text-3xl font-extrabold tracking-[-.05em]">Admin desk</h1><p className="mt-2 text-sm text-muted-foreground">A clear view of what is moving, and what needs a nudge.</p></div><div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-xs text-muted-foreground"><Activity size={14} className="text-accent" />Live report · last 30 days</div></div>
    {query.isError && <div className="mt-6 flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 p-3 text-xs"><CircleAlert size={15} className="text-primary" />Report preview shown while the live admin feed reconnects.</div>}
    <div className="mt-8 grid gap-4 md:grid-cols-3"><div className="rounded-xl bg-secondary p-5 text-secondary-foreground"><div className="flex items-center justify-between text-xs text-secondary-foreground/65"><span>Revenue</span><BarChart3 size={16} className="text-primary" /></div><div className="mt-7 font-mono text-3xl">{money(report.revenue)}</div><div className="mt-2 text-xs text-primary">+12.4% vs prior period</div></div><Metric label="Orders processed" value={report.orders.toString()} detail="8 awaiting dispatch" icon={Package} /><Metric label="Low stock watch" value={report.lowStock.toString().padStart(2, '0')} detail="Needs a restock plan" icon={CircleAlert} warning /></div>
    <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><div className="rounded-xl border border-border bg-card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="font-bold">Top movers</h2><p className="mt-1 text-xs text-muted-foreground">Revenue contribution by part</p></div><span className="rounded-md bg-muted px-2 py-1 font-mono text-[10px] text-muted-foreground">30 DAYS</span></div><div className="mt-7 space-y-5">{report.topProducts.map((item, i) => <div key={item.name} data-testid={`row-top-product-${i}`}><div className="mb-2 flex items-center justify-between gap-3 text-xs"><span className="truncate font-semibold">{item.name}</span><span className="shrink-0 font-mono text-muted-foreground">{money(item.revenue)}</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(item.revenue / max) * 100}%` }} /></div><div className="mt-1 text-[10px] text-muted-foreground">{item.quantity} units moved</div></div>)}</div></div><div className="rounded-xl border border-border bg-card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="font-bold">Needs attention</h2><p className="mt-1 text-xs text-muted-foreground">Quiet shelves worth checking</p></div><CircleAlert size={17} className="text-primary" /></div><div className="mt-6 space-y-4">{report.unpopularProducts.map(item => <div key={item.name} className="flex items-start justify-between gap-4 border-b border-border/70 pb-4 last:border-0 last:pb-0"><div><p className="text-xs font-semibold leading-5">{item.name}</p><p className="mt-1 font-mono text-[10px] text-muted-foreground">{item.quantity} sold · {money(item.revenue)}</p></div><button className="shrink-0 rounded-md border border-border px-2 py-1 text-[10px] font-bold text-muted-foreground hover:border-primary hover:text-primary" data-testid={`button-review-product-${item.name.toLowerCase().replaceAll(' ', '-')}`}>Review</button></div>)}</div></div></div>
    <div className="mt-6 grid gap-4 sm:grid-cols-3"><AdminLink icon={Boxes} title="Stock ledger" body="Review inventory and reorder points" /><AdminLink icon={ShoppingBag} title="Order queue" body="Check paid and pending tickets" /><AdminLink icon={Truck} title="Dispatch desk" body="Keep today's parcels moving" /></div>
  </section>;
}

function Metric({ label, value, detail, icon: Icon, warning }: { label: string; value: string; detail: string; icon: typeof Package; warning?: boolean }) {
  return <div className="rounded-xl border border-border bg-card p-5"><div className="flex items-center justify-between text-xs text-muted-foreground"><span>{label}</span><Icon size={16} className={warning ? 'text-primary' : 'text-accent'} /></div><div className="mt-7 font-mono text-3xl">{value}</div><div className={`mt-2 text-xs ${warning ? 'text-primary' : 'text-muted-foreground'}`}>{detail}</div></div>;
}
function AdminLink({ icon: Icon, title, body }: { icon: typeof Package; title: string; body: string }) {
  return <button className="flex items-center gap-4 rounded-xl border border-border bg-card p-4 text-left transition-colors hover:border-primary/60" data-testid={`button-admin-${title.toLowerCase().replaceAll(' ', '-')}`}><span className="grid size-10 place-items-center rounded-lg bg-muted text-secondary"><Icon size={17} /></span><span><span className="block text-sm font-bold">{title}</span><span className="mt-1 block text-xs text-muted-foreground">{body}</span></span><ChevronRight size={16} className="ml-auto text-muted-foreground" /></button>;
}

function NotFound() {
  return <div className="grid min-h-[65vh] place-items-center py-16"><div className="text-center"><div className="font-mono text-sm text-primary">404 / NOT ON THE SHELF</div><h1 className="mt-3 text-4xl font-extrabold tracking-[-.06em]">That bay is empty.</h1><p className="mt-3 text-sm text-muted-foreground">The page you requested does not exist in this catalog.</p><Link href="/" className="mt-6 inline-flex rounded-lg bg-secondary px-4 py-3 text-xs font-bold text-secondary-foreground" data-testid="link-back-catalog">Back to catalog</Link></div></div>;
}

function Router() {
  const [pathname] = useLocation();
  return <ErrorBoundary resetKey={pathname}><Switch><Route path="/" component={Catalog} /><Route path="/cart" component={CartPage} /><Route path="/orders" component={OrdersPage} /><Route path="/admin" component={AdminPage} /><Route component={NotFound} /></Switch></ErrorBoundary>;
}

function App() {
  return <QueryClientProvider client={queryClient}><TooltipProvider><Shell><Router /></Shell><Toaster /></TooltipProvider></QueryClientProvider>;
}

export default App;