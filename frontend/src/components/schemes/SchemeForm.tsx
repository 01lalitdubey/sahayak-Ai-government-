"use client";

import React, { useState } from "react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save, Send, ChevronRight, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import type { SchemeDetail, SchemeCreatePayload } from "@/types/scheme";
import { useCategories } from "@/hooks/use-schemes";

const schemeSchema = z.object({
  scheme_code: z.string().min(3, "Min 3 characters").max(50),
  name: z.string().min(3, "Min 3 characters").max(500),
  short_description: z.string().max(500).optional(),
  full_description: z.string().optional(),
  benefits: z.string().optional(),
  required_documents: z.string().optional(),
  application_process: z.string().optional(),
  scheme_type: z.enum(["central", "state"]),
  category: z.string().optional(),
  ministry: z.string().max(300).optional(),
  department: z.string().max(300).optional(),
  state: z.string().max(100).optional(),
  district: z.string().max(100).optional(),
  application_mode: z.enum(["online", "offline", "both"]),
  application_start_date: z.string().optional(),
  application_end_date: z.string().optional(),
  official_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  official_pdf_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  contact_email: z.string().email("Invalid email").optional().or(z.literal("")),
  contact_phone: z.string().max(20).optional(),
  is_active: z.boolean(),
  is_featured: z.boolean(),
});

type SchemeFormData = z.infer<typeof schemeSchema>;

const STEPS = [
  "Basic Info",
  "Government & Category",
  "Benefits & Eligibility",
  "Application Details",
  "Official Sources",
  "Preview & Submit",
];

interface SchemeFormProps {
  defaultValues?: Partial<SchemeDetail>;
  onSubmit: (data: SchemeCreatePayload) => Promise<void>;
  isEditing?: boolean;
}

export function SchemeForm({ defaultValues, onSubmit, isEditing = false }: SchemeFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const { data: categoriesData } = useCategories();

  const methods = useForm<SchemeFormData>({
    resolver: zodResolver(schemeSchema),
    defaultValues: {
      scheme_code: defaultValues?.scheme_code ?? "",
      name: defaultValues?.name ?? "",
      short_description: defaultValues?.short_description ?? "",
      full_description: defaultValues?.full_description ?? "",
      benefits: defaultValues?.benefits ?? "",
      required_documents: defaultValues?.required_documents ?? "",
      application_process: defaultValues?.application_process ?? "",
      scheme_type: defaultValues?.scheme_type ?? "central",
      category: defaultValues?.category ?? "",
      ministry: defaultValues?.ministry ?? "",
      department: defaultValues?.department ?? "",
      state: defaultValues?.state ?? "",
      district: defaultValues?.district ?? "",
      application_mode: defaultValues?.application_mode ?? "online",
      application_start_date: defaultValues?.application_start_date ?? "",
      application_end_date: defaultValues?.application_end_date ?? "",
      official_url: defaultValues?.official_url ?? "",
      official_pdf_url: defaultValues?.official_pdf_url ?? "",
      contact_email: defaultValues?.contact_email ?? "",
      contact_phone: defaultValues?.contact_phone ?? "",
      is_active: defaultValues?.is_active ?? false, // Default to false (draft) for new
      is_featured: defaultValues?.is_featured ?? false,
    },
    mode: "onTouched",
  });

  const { register, handleSubmit, setValue, trigger, watch, formState: { errors, isSubmitting } } = methods;
  const formData = watch();

  const nextStep = async () => {
    // Validate current step fields before proceeding
    let fieldsToValidate: (keyof SchemeFormData)[] = [];
    if (currentStep === 0) fieldsToValidate = ["scheme_code", "name", "short_description", "full_description"];
    if (currentStep === 1) fieldsToValidate = ["scheme_type", "category", "state", "district", "ministry", "department"];
    // Add other validations if needed
    
    const isStepValid = await trigger(fieldsToValidate);
    if (isStepValid) {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  const handleFinalSubmit = async (publish: boolean) => {
    setValue("is_active", publish);
    const isValid = await trigger();
    if (isValid) {
      await handleSubmit((data) => onSubmit(data as SchemeCreatePayload))();
    }
  };

  const field = (label: string, name: keyof SchemeFormData, type = "text", required = false) => {
    const err = errors[name];
    return (
      <div className="space-y-1.5">
        <Label htmlFor={name} className="text-sm">
          {label}{required && <span className="text-destructive ml-0.5">*</span>}
        </Label>
        <Input id={name} type={type} {...register(name)} placeholder={label} />
        {err && <p className="text-xs text-destructive">{String(err.message)}</p>}
      </div>
    );
  };

  const textArea = (label: string, name: keyof SchemeFormData) => {
    const err = errors[name];
    return (
      <div className="space-y-1.5 flex flex-col h-full">
        <Label htmlFor={name} className="text-sm">{label}</Label>
        <textarea
          id={name}
          rows={5}
          className="w-full flex-grow rounded-md border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
          placeholder={label}
          {...register(name)}
        />
        {err && <p className="text-xs text-destructive">{String(err.message)}</p>}
      </div>
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Stepper Header */}
      <div className="bg-gray-50 border-b border-gray-100 px-6 py-4">
        <nav aria-label="Progress">
          <ol role="list" className="flex items-center">
            {STEPS.map((step, index) => (
              <li key={step} className={`relative pr-8 sm:pr-20 ${index === STEPS.length - 1 ? 'pr-0 sm:pr-0' : ''}`}>
                <div className="flex items-center">
                  <div className={`
                    flex h-8 w-8 items-center justify-center rounded-full border-2 
                    ${index < currentStep ? 'bg-primary-600 border-primary-600' : index === currentStep ? 'border-primary-600 text-primary-600' : 'border-gray-300 text-gray-500'}
                  `}>
                    {index < currentStep ? (
                      <Save className="h-4 w-4 text-white" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  {index !== STEPS.length - 1 && (
                    <div className={`absolute top-4 left-8 h-0.5 w-full -translate-y-1/2 sm:left-10 ${index < currentStep ? 'bg-primary-600' : 'bg-gray-200'}`} />
                  )}
                </div>
                <div className="mt-2 hidden sm:block">
                  <span className={`text-xs font-medium ${index <= currentStep ? 'text-primary-600' : 'text-gray-500'}`}>{step}</span>
                </div>
              </li>
            ))}
          </ol>
        </nav>
      </div>

      <div className="p-6 sm:p-8">
        <FormProvider {...methods}>
          <form className="space-y-6">
            
            {/* Step 0: Basic Info */}
            <div className={currentStep === 0 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Basic Information</h2>
              <div className="grid gap-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  {field("Scheme Code", "scheme_code", "text", true)}
                  {field("Scheme Name", "name", "text", true)}
                </div>
                {field("Short Description (max 500 chars)", "short_description")}
                {textArea("Full Description", "full_description")}
              </div>
            </div>

            {/* Step 1: Government & Category */}
            <div className={currentStep === 1 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Classification & Jurisdiction</h2>
              <div className="grid gap-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label className="text-sm">Scheme Type<span className="text-destructive ml-0.5">*</span></Label>
                    <select className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring" {...register("scheme_type")}>
                      <option value="central">Central</option>
                      <option value="state">State</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm">Category</Label>
                    <select className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring" {...register("category")}>
                      <option value="">Select category</option>
                      {categoriesData?.data.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {field("Ministry", "ministry")}
                  {field("Department", "department")}
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {field("State (If state scheme)", "state")}
                  {field("District (If specific)", "district")}
                </div>
              </div>
            </div>

            {/* Step 2: Benefits */}
            <div className={currentStep === 2 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Benefits & Eligibility</h2>
              <p className="text-sm text-gray-500 mb-4">Detailed eligibility rules can be configured later in the Eligibility section.</p>
              <div className="grid gap-6 h-64">
                {textArea("Benefits Description", "benefits")}
              </div>
            </div>

            {/* Step 3: Application Details */}
            <div className={currentStep === 3 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Application Process</h2>
              <div className="grid gap-6">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="space-y-1.5">
                    <Label className="text-sm">Application Mode<span className="text-destructive ml-0.5">*</span></Label>
                    <select className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring" {...register("application_mode")}>
                      <option value="online">Online</option>
                      <option value="offline">Offline</option>
                      <option value="both">Both</option>
                    </select>
                  </div>
                  {field("Start Date", "application_start_date", "date")}
                  {field("End Date", "application_end_date", "date")}
                </div>
                <div className="grid gap-6 sm:grid-cols-2 h-64">
                  {textArea("Required Documents", "required_documents")}
                  {textArea("Application Process Steps", "application_process")}
                </div>
              </div>
            </div>

            {/* Step 4: Official Sources */}
            <div className={currentStep === 4 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Official Sources & Contact</h2>
              <div className="grid gap-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  {field("Official URL", "official_url", "url")}
                  {field("Official PDF URL", "official_pdf_url", "url")}
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {field("Contact Email", "contact_email", "email")}
                  {field("Contact Phone", "contact_phone")}
                </div>
                <div className="flex items-center gap-2 mt-4 bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <Checkbox id="is_featured" checked={formData.is_featured} onCheckedChange={(v) => setValue("is_featured", !!v)} />
                  <div>
                    <Label htmlFor="is_featured" className="font-semibold cursor-pointer">Feature this Scheme</Label>
                    <p className="text-xs text-gray-500">Highlighted on homepage / discovery page.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 5: Preview */}
            <div className={currentStep === 5 ? "block" : "hidden"}>
              <h2 className="text-xl font-semibold mb-4 text-gray-900">Preview & Confirm</h2>
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <div className="mb-6 pb-6 border-b border-gray-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 mb-2">
                        {formData.scheme_code || "SCHEME-CODE"}
                      </span>
                      <h3 className="text-2xl font-bold text-gray-900">{formData.name || "Scheme Title"}</h3>
                      <p className="text-sm text-gray-500 mt-1">{formData.ministry} • {formData.scheme_type}</p>
                    </div>
                  </div>
                  <p className="mt-4 text-gray-700">{formData.short_description || "Short description..."}</p>
                </div>
                
                <div className="grid sm:grid-cols-2 gap-8">
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2">Benefits</h4>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{formData.benefits || "No benefits provided."}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2">Documents Required</h4>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{formData.required_documents || "No document list provided."}</p>
                  </div>
                  <div className="sm:col-span-2">
                    <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2">Application Process ({formData.application_mode})</h4>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{formData.application_process || "No process provided."}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-100">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 0 || isSubmitting}
              >
                <ChevronLeft className="mr-2 h-4 w-4" /> Back
              </Button>

              <div className="flex gap-3">
                {currentStep < STEPS.length - 1 ? (
                  <Button type="button" onClick={nextStep}>
                    Next <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                ) : (
                  <>
                    <Button 
                      type="button" 
                      variant="secondary" 
                      className="bg-gray-100 text-gray-900 hover:bg-gray-200"
                      onClick={() => handleFinalSubmit(false)}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                      Save as Draft
                    </Button>
                    <Button 
                      type="button" 
                      className="bg-primary-600 hover:bg-primary-700"
                      onClick={() => handleFinalSubmit(true)}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                      {isEditing ? "Update & Publish" : "Publish Scheme"}
                    </Button>
                  </>
                )}
              </div>
            </div>
          </form>
        </FormProvider>
      </div>
    </div>
  );
}
